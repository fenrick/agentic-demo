"""Application settings validated via Pydantic.

This module defines the :class:`Settings` class which reads configuration from
environment variables at import time. Missing or invalid environment variables
raise a :class:`pydantic.ValidationError`, causing the application to fail fast
with a clear message. A single instance of :data:`settings` is created and
should be injected into the application state during startup.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", case_sensitive=False
    )

    OPENAI_API_KEY: SecretStr = Field(..., description="API key for OpenAI access")
    DATA_DIR: Path = Field(
        Path("./workspace"),
        description="Directory used for persistent workspace data",
    )
    DATABASE_URL: str | None = Field(
        None, description="Database connection URL; defaults to SQLite in DATA_DIR"
    )
    JWT_SECRET: SecretStr = Field(..., description="Secret key for signing JWTs")
    ALLOWLIST_DOMAINS: str | None = Field(
        None, description="JSON list of domains allowed for outbound requests"
    )
    OFFLINE_MODE: bool = Field(False, description="Run without external network access")
    ENABLE_TRACING: bool = Field(
        True, description="Enable application performance tracing and metrics"
    )
    FRONTEND_DIST: str = Field(
        "frontend/dist", description="Path to the built frontend assets"
    )

    # Optional external services
    TAVILY_API_KEY: SecretStr | None = Field(
        None, description="API key for Tavily search service"
    )


# Eagerly validate configuration on import for early failure.
settings = Settings()


__all__ = ["Settings", "settings"]
