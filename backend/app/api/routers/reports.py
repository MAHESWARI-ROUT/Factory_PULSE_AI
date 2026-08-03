from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_report_service
from app.schemas.report import MaintenanceReportOut
from app.services.report_generator import MaintenanceReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/maintenance", response_model=MaintenanceReportOut)
def maintenance_report(
    service: MaintenanceReportService = Depends(get_report_service),
) -> MaintenanceReportOut:
    return service.generate()
