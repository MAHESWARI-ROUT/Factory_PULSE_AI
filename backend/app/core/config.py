"""Centralized, typed configuration. Every environment-dependent value the
app needs flows through this single Settings object so nothing reaches for
os.environ directly elsewhere in the codebase."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "FactoryPulse AI"
    api_v1_prefix: str = "/api"
    environment: str = "development"

    # Falls back to a local SQLite file so the project runs out of the box;
    # set DATABASE_URL to a postgres:// DSN in production (Render provides one).
    database_url: str = "sqlite:///./factorypulse.db"

    # Comma-separated origins allowed to call the API from the browser.
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Optional: if unset, the app automatically falls back to the rule-based
    # explanation engine instead of calling out to Gemini.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"

    ml_models_dir: str = "app/ml_models"

    # Health score thresholds, kept configurable rather than hard-coded so a
    # plant manager can tune sensitivity without touching code.
    health_excellent_min: float = 95.0
    health_healthy_min: float = 80.0
    health_warning_min: float = 60.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
