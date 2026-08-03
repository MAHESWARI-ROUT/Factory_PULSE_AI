"""Converts raw model outputs into the 0-100 health score and status band the
dashboard displays. Isolated on its own so the scoring formula and thresholds
can be tuned (or A/B tested) without touching the ML service."""
from __future__ import annotations

from app.core.config import Settings
from app.domain.enums import HealthStatus
from app.services.interfaces import IHealthScoreService


class ThresholdHealthScoreService(IHealthScoreService):
    def __init__(self, settings: Settings):
        self._settings = settings

    def score(self, failure_probability: float, anomaly_score: float) -> tuple[float, str]:
        # Blend the supervised failure probability (70% weight, it's the
        # stronger signal) with the unsupervised anomaly score (30% weight,
        # catches drift the classifier hasn't seen labeled examples of yet).
        risk = 0.7 * failure_probability + 0.3 * anomaly_score
        raw_score = 100.0 * (1.0 - risk)
        health_score = max(0.0, min(100.0, raw_score))

        if health_score >= self._settings.health_excellent_min:
            status = HealthStatus.EXCELLENT
        elif health_score >= self._settings.health_healthy_min:
            status = HealthStatus.HEALTHY
        elif health_score >= self._settings.health_warning_min:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.CRITICAL

        return health_score, status.value
