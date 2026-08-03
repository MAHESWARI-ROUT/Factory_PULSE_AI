"""FactoryPulse AI — API entrypoint. Wires up middleware, routers, and
startup tasks. Business logic never lives here; this module is purely
composition and transport concerns."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import admin, chat, dashboard, machines, predictions, reports
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.repositories.sqlalchemy_repositories import (
    SqlAlchemyMachineRepository,
    SqlAlchemySnapshotRepository,
)
from app.services.data_seeder import DataSeederService
from app.services.health_score import ThresholdHealthScoreService
from app.services.ml_predictor import MLPredictionService, ModelArtifacts
from app.services.recommendation import RuleBasedRecommendationService

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("factorypulse.main")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _auto_seed_if_empty()
    yield


def _auto_seed_if_empty() -> None:
    """Convenience for local/dev/demo use: if the DB is empty, load the
    bundled dataset automatically so the dashboard isn't blank on first run."""
    db = SessionLocal()
    try:
        machine_repo = SqlAlchemyMachineRepository(db)
        if machine_repo.count() > 0:
            return
        csv_path = Path("data/ai4i2020.csv")
        if not csv_path.exists():
            logger.warning("No dataset found at %s — skipping auto-seed.", csv_path)
            return

        artifacts = ModelArtifacts(Path(settings.ml_models_dir))
        health_service = ThresholdHealthScoreService(settings)
        ml_service = MLPredictionService(artifacts, health_service)
        recommendation_service = RuleBasedRecommendationService()
        snapshot_repo = SqlAlchemySnapshotRepository(db)

        seeder = DataSeederService(machine_repo, snapshot_repo, ml_service, recommendation_service)
        seeder.seed_from_csv(csv_path)
    finally:
        db.close()


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(machines.router, prefix=settings.api_v1_prefix)
app.include_router(predictions.router, prefix=settings.api_v1_prefix)
app.include_router(dashboard.router, prefix=settings.api_v1_prefix)
app.include_router(reports.router, prefix=settings.api_v1_prefix)
app.include_router(chat.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict:
    return {"service": settings.app_name, "status": "running"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
