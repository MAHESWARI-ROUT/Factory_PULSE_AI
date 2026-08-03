"""Wraps the artifacts produced by ml/train.py behind the IMLPredictionService
interface. This is the only place in the backend that knows joblib, pandas,
or feature-engineering details exist -- everything downstream just consumes a
PredictionOutcome.

The feature engineering here intentionally mirrors ml/train.py's
FeatureEngineer._engineer step exactly (same derived columns, same order).
It is kept as plain functions over sklearn's built-in LabelEncoder /
StandardScaler rather than importing the training-time custom class, so the
backend has no dependency on the ml/ package and the joblib artifacts stay
portable across processes.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import pandas as pd

from app.domain.entities import PredictionOutcome, SensorReading
from app.domain.enums import FailureType
from app.services.interfaces import IHealthScoreService, IMLPredictionService

logger = logging.getLogger("factorypulse.ml")


class ModelArtifacts:
    """Loads and holds the model artifacts + metadata a single time."""

    def __init__(self, models_dir: Path):
        self.type_encoder = joblib.load(models_dir / "type_encoder.joblib")
        self.feature_scaler = joblib.load(models_dir / "feature_scaler.joblib")
        self.failure_predictor = joblib.load(models_dir / "failure_predictor.joblib")
        self.failure_type_classifier = joblib.load(models_dir / "failure_type_classifier.joblib")
        self.failure_type_encoder = joblib.load(models_dir / "failure_type_encoder.joblib")
        self.anomaly_detector = joblib.load(models_dir / "anomaly_detector.joblib")
        with open(models_dir / "metadata.json") as f:
            self.metadata = json.load(f)
        self.numeric_feature_order: list[str] = self.metadata["numeric_feature_order"]
        logger.info("Loaded model artifacts from %s", models_dir)


class MLPredictionService(IMLPredictionService):
    """XGBoost failure/failure-type classifiers + Isolation Forest anomaly score."""

    def __init__(self, artifacts: ModelArtifacts, health_score_service: IHealthScoreService):
        self._artifacts = artifacts
        self._health_score_service = health_score_service

    def predict(self, reading: SensorReading) -> PredictionOutcome:
        features = self._build_features(reading)

        failure_probability = float(
            self._artifacts.failure_predictor.predict_proba(features)[:, 1][0]
        )

        type_pred_idx = int(self._artifacts.failure_type_classifier.predict(features)[0])
        predicted_type_str = self._artifacts.failure_type_encoder.inverse_transform(
            [type_pred_idx]
        )[0]
        if failure_probability < 0.15:
            predicted_type_str = FailureType.NONE.value

        raw_anomaly_score = float(
            self._artifacts.anomaly_detector.decision_function(features)[0]
        )
        is_anomaly = bool(self._artifacts.anomaly_detector.predict(features)[0] == -1)
        normalized_anomaly = max(0.0, min(1.0, 0.5 - raw_anomaly_score))

        health_score, health_status = self._health_score_service.score(
            failure_probability, normalized_anomaly
        )

        return PredictionOutcome(
            failure_probability=round(failure_probability, 4),
            predicted_failure_type=FailureType(predicted_type_str),
            anomaly_score=round(normalized_anomaly, 4),
            is_anomaly=is_anomaly,
            health_score=round(health_score, 1),
            health_status=health_status,
        )

    def _build_features(self, reading: SensorReading) -> pd.DataFrame:
        air_temp = reading.air_temperature_k
        process_temp = reading.process_temperature_k
        rpm = reading.rotational_speed_rpm
        torque = reading.torque_nm
        tool_wear = reading.tool_wear_min

        numeric_row = {
            "air_temp_k": air_temp,
            "process_temp_k": process_temp,
            "rotational_speed_rpm": rpm,
            "torque_nm": torque,
            "tool_wear_min": tool_wear,
            "temp_delta": process_temp - air_temp,
            "power_proxy": rpm * torque / 9548.8,
        }
        numeric_df = pd.DataFrame([numeric_row])[self._artifacts.numeric_feature_order]
        scaled = self._artifacts.feature_scaler.transform(numeric_df)
        scaled_df = pd.DataFrame(scaled, columns=self._artifacts.numeric_feature_order)

        type_code = self._artifacts.type_encoder.transform([reading.machine_type.value])[0]
        scaled_df.insert(0, "Type", type_code)
        return scaled_df
