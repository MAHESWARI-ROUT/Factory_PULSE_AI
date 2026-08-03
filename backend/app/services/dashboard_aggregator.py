"""Aggregates snapshot data into the two dashboard views the frontend renders:
the executive summary and the operational risk board."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from app.domain.enums import HealthStatus
from app.orm.models import MachineSnapshot
from app.repositories.interfaces import IMachineRepository, ISnapshotRepository
from app.schemas.dashboard import (
    ExecutiveDashboardOut,
    FailureTypeCount,
    HealthTrendPoint,
    RiskDashboardOut,
)


class DashboardAggregatorService:
    def __init__(self, machine_repo: IMachineRepository, snapshot_repo: ISnapshotRepository):
        self._machine_repo = machine_repo
        self._snapshot_repo = snapshot_repo

    def executive_summary(self) -> ExecutiveDashboardOut:
        latest = self._snapshot_repo.latest_per_machine()
        total = len(latest)
        healthy = sum(
            1 for s in latest if s.health_status in (HealthStatus.EXCELLENT.value, HealthStatus.HEALTHY.value)
        )
        critical = sum(1 for s in latest if s.health_status == HealthStatus.CRITICAL.value)
        avg_health = round(sum(s.health_score for s in latest) / total, 1) if total else 0.0

        return ExecutiveDashboardOut(
            total_machines=total,
            healthy_count=healthy,
            critical_count=critical,
            average_health_score=avg_health,
            failure_type_distribution=self._failure_distribution(latest),
            ai_recommendations=self._top_recommendations(latest),
        )

    def risk_dashboard(self) -> RiskDashboardOut:
        latest = self._snapshot_repo.latest_per_machine()
        counts = Counter(s.health_status for s in latest)

        top_risk = sorted(latest, key=lambda s: s.health_score)[:10]
        top_risk_payload = [
            {
                "machine_id": s.machine.machine_id,
                "health_score": s.health_score,
                "health_status": s.health_status,
                "predicted_failure_type": s.predicted_failure_type,
                "failure_probability": s.failure_probability,
            }
            for s in top_risk
        ]

        return RiskDashboardOut(
            healthy_count=counts.get(HealthStatus.HEALTHY.value, 0),
            warning_count=counts.get(HealthStatus.WARNING.value, 0),
            critical_count=counts.get(HealthStatus.CRITICAL.value, 0),
            excellent_count=counts.get(HealthStatus.EXCELLENT.value, 0),
            failure_distribution=self._failure_distribution(latest),
            health_trend=self._health_trend(),
            top_risk_machines=top_risk_payload,
        )

    def _health_trend(self, days: int = 14) -> list[HealthTrendPoint]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        snapshots = self._snapshot_repo.snapshots_since(since)
        by_day: dict[str, list[float]] = {}
        for s in snapshots:
            day_key = s.recorded_at.strftime("%Y-%m-%d")
            by_day.setdefault(day_key, []).append(s.health_score)
        points = [
            HealthTrendPoint(date=day, average_health_score=round(sum(scores) / len(scores), 1))
            for day, scores in sorted(by_day.items())
        ]
        return points

    @staticmethod
    def _failure_distribution(snapshots: list[MachineSnapshot]) -> list[FailureTypeCount]:
        counter = Counter(s.predicted_failure_type for s in snapshots)
        return [
            FailureTypeCount(failure_type=ftype, count=count)
            for ftype, count in sorted(counter.items(), key=lambda kv: -kv[1])
        ]

    @staticmethod
    def _top_recommendations(snapshots: list[MachineSnapshot], limit: int = 5) -> list[str]:
        critical = sorted(
            (s for s in snapshots if s.health_status == HealthStatus.CRITICAL.value),
            key=lambda s: s.health_score,
        )[:limit]
        if not critical:
            return ["All machines are within healthy operating parameters. No urgent action needed."]
        return [
            f"{s.machine.machine_id}: {s.recommended_action}" for s in critical
        ]
