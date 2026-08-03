"""Service-layer contracts. Routers depend on these abstractions; concrete
implementations are wired together in app/api/deps.py. This keeps the API
layer, business logic, and infrastructure (ML models, Gemini, DB) each
replaceable in isolation — the Open/Closed half of SOLID in practice."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import MaintenanceRecommendation, PredictionOutcome, SensorReading


class IMLPredictionService(ABC):
    @abstractmethod
    def predict(self, reading: SensorReading) -> PredictionOutcome: ...


class IHealthScoreService(ABC):
    @abstractmethod
    def score(self, failure_probability: float, anomaly_score: float) -> tuple[float, str]:
        """Returns (health_score 0-100, health_status label)."""


class IExplanationService(ABC):
    @abstractmethod
    def explain(self, machine_id: str, reading: SensorReading, outcome: PredictionOutcome) -> str: ...

    @abstractmethod
    def answer_question(self, question: str, context: str) -> str: ...


class IRecommendationService(ABC):
    @abstractmethod
    def recommend(
        self, machine_id: str, reading: SensorReading, outcome: PredictionOutcome
    ) -> MaintenanceRecommendation: ...
