from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Support both repo-root `.env` (recommended) and `app/.env` (common local setup).
    # Environment variables (e.g., DATABASE_URL) still take precedence.
    model_config = SettingsConfigDict(env_file=(".env", "app/.env"), env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    database_url: str


settings = Settings()

