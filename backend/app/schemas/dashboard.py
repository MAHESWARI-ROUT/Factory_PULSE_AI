from __future__ import annotations

from pydantic import BaseModel


class FailureTypeCount(BaseModel):
    failure_type: str
    count: int


class HealthTrendPoint(BaseModel):
    date: str
    average_health_score: float


class RiskDashboardOut(BaseModel):
    healthy_count: int
    warning_count: int
    critical_count: int
    excellent_count: int
    failure_distribution: list[FailureTypeCount]
    health_trend: list[HealthTrendPoint]
    top_risk_machines: list[dict]


class ExecutiveDashboardOut(BaseModel):
    total_machines: int
    healthy_count: int
    critical_count: int
    average_health_score: float
    failure_type_distribution: list[FailureTypeCount]
    ai_recommendations: list[str]
