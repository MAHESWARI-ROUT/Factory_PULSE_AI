"""Builds the automatic maintenance report: one row per machine, ranked by
urgency, ready to render as a table or export to PDF/CSV from the frontend."""
from __future__ import annotations

from datetime import datetime, timezone

from app.domain.enums import MaintenancePriority
from app.repositories.interfaces import ISnapshotRepository
from app.schemas.report import MaintenanceReportOut, MaintenanceReportRow

_PRIORITY_ORDER = {
    MaintenancePriority.URGENT.value: 0,
    MaintenancePriority.HIGH.value: 1,
    MaintenancePriority.MEDIUM.value: 2,
    MaintenancePriority.LOW.value: 3,
}


class MaintenanceReportService:
    def __init__(self, snapshot_repo: ISnapshotRepository):
        self._snapshot_repo = snapshot_repo

    def generate(self) -> MaintenanceReportOut:
        latest = self._snapshot_repo.latest_per_machine()
        rows = [
            MaintenanceReportRow(
                machine_id=s.machine.machine_id,
                failure_probability=s.failure_probability,
                predicted_failure_type=s.predicted_failure_type,
                priority=s.priority,
                recommended_action=s.recommended_action,
                health_score=s.health_score,
            )
            for s in latest
        ]
        rows.sort(key=lambda r: (_PRIORITY_ORDER.get(r.priority.value, 9), -r.failure_probability))

        urgent_count = sum(1 for r in rows if r.priority == MaintenancePriority.URGENT)
        return MaintenanceReportOut(
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_machines_reviewed=len(rows),
            urgent_count=urgent_count,
            rows=rows,
        )
