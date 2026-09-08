"""Composition root: this is the one place that wires interfaces to concrete
implementations. Routers only ever ask for the interface types below via
FastAPI's Depends(), so nothing outside this file needs to know which
concrete class is behind IExplanationService, IMLPredictionService, etc."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.repositories.interfaces import IMachineRepository, ISnapshotRepository
from app.repositories.sqlalchemy_repositories import (
    SqlAlchemyMachineRepository,
    SqlAlchemySnapshotRepository,
)
from app.services.chat_assistant import ChatAssistantService
from app.services.dashboard_aggregator import DashboardAggregatorService
from app.services.data_seeder import DataSeederService
from app.services.batch_prediction import BatchPredictionService
from app.services.explanation import GeminiExplanationService, RuleBasedExplanationService
from app.services.health_score import ThresholdHealthScoreService
from app.services.interfaces import IExplanationService, IHealthScoreService, IMLPredictionService
from app.services.ml_predictor import MLPredictionService, ModelArtifacts
from app.services.recommendation import RuleBasedRecommendationService
from app.services.report_generator import MaintenanceReportService


@lru_cache
def get_model_artifacts() -> ModelArtifacts:
    settings = get_settings()
    return ModelArtifacts(Path(settings.ml_models_dir))


def get_health_score_service(settings: Settings = Depends(get_settings)) -> IHealthScoreService:
    return ThresholdHealthScoreService(settings)


def get_ml_prediction_service(
    health_score_service: IHealthScoreService = Depends(get_health_score_service),
) -> IMLPredictionService:
    return MLPredictionService(get_model_artifacts(), health_score_service)


def get_recommendation_service() -> RuleBasedRecommendationService:
    return RuleBasedRecommendationService()


def get_explanation_service(settings: Settings = Depends(get_settings)) -> IExplanationService:
    fallback = RuleBasedExplanationService()
    if settings.gemini_api_key:
        return GeminiExplanationService(settings.gemini_api_key, settings.gemini_model, fallback)
    return fallback


def get_batch_prediction_service(
    ml_service: IMLPredictionService = Depends(get_ml_prediction_service),
    recommendation_service: RuleBasedRecommendationService = Depends(get_recommendation_service),
    explanation_service: IExplanationService = Depends(get_explanation_service),
) -> BatchPredictionService:
    # Wires failure predictor + failure-type classifier + anomaly detector
    # (all inside ml_service) + health-score service (inside ml_service) +
    # recommendation service + Gemini/rule-based explanation service into
    # the batch pipeline — the same stack the single "/predictions/predict"
    # and machine-detail routes use.
    return BatchPredictionService(ml_service, recommendation_service, explanation_service)


def get_machine_repository(db: Session = Depends(get_db)) -> IMachineRepository:
    return SqlAlchemyMachineRepository(db)


def get_snapshot_repository(db: Session = Depends(get_db)) -> ISnapshotRepository:
    return SqlAlchemySnapshotRepository(db)


def get_dashboard_service(
    machine_repo: IMachineRepository = Depends(get_machine_repository),
    snapshot_repo: ISnapshotRepository = Depends(get_snapshot_repository),
) -> DashboardAggregatorService:
    return DashboardAggregatorService(machine_repo, snapshot_repo)


def get_report_service(
    snapshot_repo: ISnapshotRepository = Depends(get_snapshot_repository),
) -> MaintenanceReportService:
    return MaintenanceReportService(snapshot_repo)


def get_chat_service(
    machine_repo: IMachineRepository = Depends(get_machine_repository),
    snapshot_repo: ISnapshotRepository = Depends(get_snapshot_repository),
    explanation_service: IExplanationService = Depends(get_explanation_service),
) -> ChatAssistantService:
    return ChatAssistantService(machine_repo, snapshot_repo, explanation_service)


def get_seeder_service(
    machine_repo: IMachineRepository = Depends(get_machine_repository),
    snapshot_repo: ISnapshotRepository = Depends(get_snapshot_repository),
    ml_service: IMLPredictionService = Depends(get_ml_prediction_service),
    recommendation_service: RuleBasedRecommendationService = Depends(get_recommendation_service),
) -> DataSeederService:
    return DataSeederService(machine_repo, snapshot_repo, ml_service, recommendation_service)
