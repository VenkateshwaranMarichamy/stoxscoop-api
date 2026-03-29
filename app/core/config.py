from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Support both repo-root `.env` (recommended) and `app/.env` (common local setup).
    # Environment variables (e.g., DATABASE_URL) still take precedence.
    model_config = SettingsConfigDict(env_file=(".env", "app/.env"), env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://localhost:5174"])

    database_url: str
    # PostgreSQL schema for v1 event stack (batches, events, subtypes, detail tables).
    events_schema: str = "stoxscoop"


settings = Settings()
