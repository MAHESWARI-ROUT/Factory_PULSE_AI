from __future__ import annotations

from pydantic import BaseModel

from app.domain.enums import FailureType, MaintenancePriority


class MaintenanceReportRow(BaseModel):
    machine_id: str
    failure_probability: float
    predicted_failure_type: FailureType
    priority: MaintenancePriority
    recommended_action: str
    health_score: float


class MaintenanceReportOut(BaseModel):
    generated_at: str
    total_machines_reviewed: int
    urgent_count: int
    rows: list[MaintenanceReportRow]
