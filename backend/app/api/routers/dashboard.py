from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_dashboard_service
from app.schemas.dashboard import ExecutiveDashboardOut, RiskDashboardOut
from app.services.dashboard_aggregator import DashboardAggregatorService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/executive", response_model=ExecutiveDashboardOut)
def executive_dashboard(
    service: DashboardAggregatorService = Depends(get_dashboard_service),
) -> ExecutiveDashboardOut:
    return service.executive_summary()


@router.get("/risk", response_model=RiskDashboardOut)
def risk_dashboard(
    service: DashboardAggregatorService = Depends(get_dashboard_service),
) -> RiskDashboardOut:
    return service.risk_dashboard()
