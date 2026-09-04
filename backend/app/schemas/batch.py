from __future__ import annotations

from pydantic import BaseModel

from app.domain.enums import FailureType, HealthStatus, MaintenancePriority


class BatchPredictionRow(BaseModel):
    row_number: int
    machine_id: str
    health_score: float
    health_status: HealthStatus
    failure_probability: float
    predicted_failure_type: FailureType
    anomaly_score: float
    is_anomaly: bool
    priority: MaintenancePriority
    recommended_action: str


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
