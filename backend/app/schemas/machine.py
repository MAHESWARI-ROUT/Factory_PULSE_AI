from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import FailureType, HealthStatus, MachineType, MaintenancePriority


class SensorReadingIn(BaseModel):
    """Payload for an ad-hoc / manual prediction request."""

    machine_id: str = Field(..., examples=["M-105"])
    machine_type: MachineType = MachineType.MEDIUM
    air_temperature_k: float = Field(..., ge=250, le=350)
    process_temperature_k: float = Field(..., ge=250, le=350)
    rotational_speed_rpm: float = Field(..., ge=0, le=5000)
    torque_nm: float = Field(..., ge=0, le=200)
    tool_wear_min: float = Field(..., ge=0, le=300)


class PredictionOut(BaseModel):
    failure_probability: float
    predicted_failure_type: FailureType
    anomaly_score: float
    is_anomaly: bool
    health_score: float
    health_status: HealthStatus
    priority: MaintenancePriority
    recommended_action: str


class SnapshotOut(BaseModel):
    id: int
    air_temperature_k: float
    process_temperature_k: float
    rotational_speed_rpm: float
    torque_nm: float
    tool_wear_min: float
    failure_probability: float
    predicted_failure_type: FailureType
    anomaly_score: float
    is_anomaly: bool
    health_score: float
    health_status: HealthStatus
    priority: MaintenancePriority
    recommended_action: str
    recorded_at: datetime

    model_config = {"from_attributes": True}


class MachineOut(BaseModel):
    machine_id: str
    machine_type: MachineType
    location: str
    latest_snapshot: SnapshotOut | None = None

    model_config = {"from_attributes": True}


class MachineDetailOut(MachineOut):
    history: list[SnapshotOut] = []


class MachineListResponse(BaseModel):
    total: int
    machines: list[MachineOut]
