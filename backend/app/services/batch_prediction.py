"""Runs the same ML pipeline used for a single ad-hoc prediction over every
row of an uploaded sensor export (CSV or Excel) — e.g. a batch pulled from
a plant's IoT/SCADA historian across many machines at once.

Column names are normalized so the uploader doesn't have to match our exact
internal naming: both the raw AI4I-style headers ("Air temperature [K]")
and friendly snake_case headers ("air_temperature_k") are accepted, which
matters in practice since different IoT devices/vendors export different
column conventions.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone

import pandas as pd

from app.domain.entities import SensorReading
from app.domain.enums import MachineType
from app.schemas.batch import BatchPredictionError, BatchPredictionResponse, BatchPredictionRow
from app.services.interfaces import IMLPredictionService, IRecommendationService

# Each canonical field accepts several header spellings, matched
# case-insensitively after stripping whitespace/brackets/underscores.
_COLUMN_ALIASES: dict[str, list[str]] = {
    "machine_id": ["machine_id", "machineid", "machine id", "id", "product id", "productid"],
    "machine_type": ["type", "machine_type", "machinetype"],
    "air_temperature_k": ["air temperature [k]", "air_temperature_k", "airtemperaturek", "air temp"],
    "process_temperature_k": [
        "process temperature [k]",
        "process_temperature_k",
        "processtemperaturek",
        "process temp",
    ],
    "rotational_speed_rpm": [
        "rotational speed [rpm]",
        "rotational_speed_rpm",
        "rotationalspeedrpm",
        "rpm",
    ],
    "torque_nm": ["torque [nm]", "torque_nm", "torquenm", "torque"],
    "tool_wear_min": ["tool wear [min]", "tool_wear_min", "toolwearmin", "tool wear"],
}

REQUIRED_FIELDS = [
    "machine_type",
    "air_temperature_k",
    "process_temperature_k",
    "rotational_speed_rpm",
    "torque_nm",
    "tool_wear_min",
]


class UnsupportedFileTypeError(Exception):
    pass


class BatchPredictionService:
    def __init__(self, ml_service: IMLPredictionService, recommendation_service: IRecommendationService):
        self._ml_service = ml_service
        self._recommendation_service = recommendation_service

    def predict_from_file(self, filename: str, content: bytes) -> BatchPredictionResponse:
        df = self._read_file(filename, content)
        df = self._normalize_columns(df)
        self._validate_required_columns(df)

        results: list[BatchPredictionRow] = []
        errors: list[BatchPredictionError] = []

        for i, row in df.iterrows():
            row_number = int(i) + 2  # +1 for 0-index, +1 for header row -> matches spreadsheet row
            try:
                results.append(self._predict_row(row_number, row))
            except Exception as exc:  # noqa: BLE001 - one bad row must not kill the batch
                errors.append(BatchPredictionError(row_number=row_number, error=str(exc)))

        return BatchPredictionResponse(
            filename=filename,
            total_rows=len(df),
            successful=len(results),
            failed=len(errors),
            results=results,
            errors=errors,
        )

    def _predict_row(self, row_number: int, row: pd.Series) -> BatchPredictionRow:
        machine_id = str(row.get("machine_id") or f"UPLOAD-ROW-{row_number}").strip()
        machine_type_raw = str(row["machine_type"]).strip().upper()
        if machine_type_raw not in {"L", "M", "H"}:
            raise ValueError(f"machine_type must be L, M, or H (got '{machine_type_raw}')")

        reading = SensorReading(
            machine_id=machine_id,
            machine_type=MachineType(machine_type_raw),
            air_temperature_k=float(row["air_temperature_k"]),
            process_temperature_k=float(row["process_temperature_k"]),
            rotational_speed_rpm=float(row["rotational_speed_rpm"]),
            torque_nm=float(row["torque_nm"]),
            tool_wear_min=float(row["tool_wear_min"]),
            recorded_at=datetime.now(timezone.utc),
        )
        outcome = self._ml_service.predict(reading)
        recommendation = self._recommendation_service.recommend(machine_id, reading, outcome)

        return BatchPredictionRow(
            row_number=row_number,
            machine_id=machine_id,
            health_score=outcome.health_score,
            health_status=outcome.health_status,
            failure_probability=outcome.failure_probability,
            predicted_failure_type=outcome.predicted_failure_type,
            anomaly_score=outcome.anomaly_score,
            is_anomaly=outcome.is_anomaly,
            priority=recommendation.priority,
            recommended_action=recommendation.recommended_action,
        )

    @staticmethod
    def _read_file(filename: str, content: bytes) -> pd.DataFrame:
        lower = filename.lower()
        if lower.endswith(".csv"):
            return pd.read_csv(io.BytesIO(content))
        if lower.endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(content))
        raise UnsupportedFileTypeError(
            f"Unsupported file type for '{filename}'. Upload a .csv, .xlsx, or .xls file."
        )

    @staticmethod
    def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        reverse_lookup: dict[str, str] = {}
        for canonical, aliases in _COLUMN_ALIASES.items():
            for alias in aliases:
                reverse_lookup[alias] = canonical

        rename_map = {}
        for col in df.columns:
            key = str(col).strip().lower()
            if key in reverse_lookup:
                rename_map[col] = reverse_lookup[key]
        return df.rename(columns=rename_map)

    @staticmethod
    def _validate_required_columns(df: pd.DataFrame) -> None:
        missing = [f for f in REQUIRED_FIELDS if f not in df.columns]
        if missing:
            raise ValueError(
                "Missing required column(s): "
                + ", ".join(missing)
                + ". Download the template for the expected format."
            )
