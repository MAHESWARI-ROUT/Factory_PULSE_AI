"""Plain-Python domain entities. These carry business meaning independent of
how they are stored (SQLAlchemy) or transported (Pydantic schemas). Keeping
them separate is what lets the persistence layer change without the business
logic noticing, and vice versa."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import FailureType, HealthStatus, MachineType, MaintenancePriority


@dataclass(frozen=True)
class SensorReading:
    """A single point-in-time set of sensor values captured from a machine."""

    machine_id: str
    machine_type: MachineType
    air_temperature_k: float
    process_temperature_k: float
    rotational_speed_rpm: float
    torque_nm: float
    tool_wear_min: float
    recorded_at: datetime


@dataclass(frozen=True)
class PredictionOutcome:
    """The result of running a SensorReading through the ML pipeline."""

    failure_probability: float
    predicted_failure_type: FailureType
    anomaly_score: float
    is_anomaly: bool
    health_score: float
    health_status: HealthStatus


@dataclass(frozen=True)
class MaintenanceRecommendation:
    """A human-actionable summary derived from a PredictionOutcome."""

    machine_id: str
    priority: MaintenancePriority
    recommended_action: str
    explanation: str
