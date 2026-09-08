from __future__ import annotations

from pydantic import BaseModel

from app.domain.enums import FailureType, HealthStatus, MachineType, MaintenancePriority


class BatchPredictionRow(BaseModel):
    row_number: int
    machine_id: str
    machine_type: MachineType

    # Raw sensor readings, echoed back so the per-row detail view (and any
    # exported report) can show the same "sensor stat" grid the single
    # machine detail page shows, without a second round-trip.
    air_temperature_k: float
    process_temperature_k: float
    rotational_speed_rpm: float
    torque_nm: float
    tool_wear_min: float

    # failure predictor + failure-type classifier
    health_score: float
    health_status: HealthStatus
    failure_probability: float
    predicted_failure_type: FailureType

    # anomaly detector
    anomaly_score: float
    is_anomaly: bool

    # recommendation service
    priority: MaintenancePriority
    recommended_action: str

    # Gemini (or rule-based fallback) natural-language explanation, the same
    # one shown in the "AI Maintenance Assistant" panel on a machine's detail
    # page — now available per row of a batch upload too.
    ai_explanation: str


class BatchPredictionError(BaseModel):
    row_number: int
    error: str


class BatchPredictionResponse(BaseModel):
    filename: str
    total_rows: int
    successful: int
    failed: int
    results: list[BatchPredictionRow]
    errors: list[BatchPredictionError]
