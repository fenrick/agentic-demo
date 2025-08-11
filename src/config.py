"""Application settings management.

Exposes configuration via a :class:`pydantic_settings.BaseSettings` subclass.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import ValidationError, ValidationInfo, field_validator
from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings, SettingsConfigDict, SettingsError

from core.logging import logger

# Load environment variables from a `.env` file if present.
load_dotenv()

# Default LLM provider and model enforced across the application.
MODEL: str = "openai:o4-mini"
DEFAULT_MODEL_NAME = MODEL.split(":", 1)[1]

SENSITIVE_FIELDS = {
    "openai_api_key",
    "tavily_api_key",
    "logfire_api_key",
    "jwt_secret",
}


def _log_settings(settings: "Settings") -> None:
    """Emit the current configuration excluding sensitive fields."""

    data = settings.model_dump()
    for field in SENSITIVE_FIELDS:
        data.pop(field, None)
    logger.info("Loaded configuration: {}", data)


class Settings(BaseSettings):
    """Configuration backed by environment variables.

    Only a subset of the original project's settings are implemented. Missing
    required variables raise a :class:`pydantic.ValidationError`.
    """

    openai_api_key: str
    data_dir: Path = Path("./workspace")
    frontend_dist: Path = Path("./frontend/dist")
    database_url: str | None = None
    tavily_api_key: str | None = None
    model: str = MODEL
    offline_mode: bool = False
    enable_tracing: bool = True
    logfire_api_key: str | None = None
    logfire_project: str | None = None
    allowlist_domains: list[str] = ["wikipedia.org", ".edu", ".gov"]
    alert_webhook_url: str | None = None
    jwt_secret: str
    jwt_algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    @field_validator("model", mode="before")
    @classmethod
    def _validate_model(cls, value: str | None) -> str:
        """Ensure ``MODEL`` follows ``<provider>:<name>`` format.

        If ``MODEL`` is unset or empty, fall back to the global ``MODEL`` default.
        """
        if not value:
            return MODEL
        if ":" not in value:
            raise ValueError("MODEL must be in '<provider>:<model_name>' format")
        return value

    @field_validator("data_dir", "frontend_dist", mode="before")
    @classmethod
    def _to_path(cls, value: str | Path) -> Path:
        return Path(value)

    @field_validator("allowlist_domains", mode="before")
    @classmethod
    def _parse_allowlist(cls, value: list[str] | str | None) -> list[str]:
        """Parse ``ALLOWLIST_DOMAINS`` from JSON or return defaults."""
        if value is None or value == "":
            return ["wikipedia.org", ".edu", ".gov"]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as exc:  # pragma: no cover - invalid input
                raise SettingsError("ALLOWLIST_DOMAINS must be valid JSON") from exc
            if not isinstance(parsed, list) or not all(
                isinstance(v, str) for v in parsed
            ):
                raise SettingsError("ALLOWLIST_DOMAINS must be a JSON list of strings")
            return parsed
        return value

    @field_validator("offline_mode", "enable_tracing", mode="before")
    @classmethod
    def _parse_bool(
        cls, value: bool | str | None, info: ValidationInfo
    ) -> bool:  # pragma: no cover - simple mapping
        """Parse common truthy/falsey strings for boolean settings."""
        if value in (None, "") or value is PydanticUndefined:
            return cls.model_fields[info.field_name].default  # type: ignore[return-value, index]
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    @property
    def model_provider(self) -> str:
        """Return the configured model provider."""
        return self.model.split(":", 1)[0]

    @property
    def model_name(self) -> str:
        """Return the configured model name."""
        return self.model.split(":", 1)[1]


def load_env(env_file: Path) -> Settings:
    """Load :class:`Settings` from a specific ``.env`` file."""

    load_dotenv(env_file)
    try:
        settings = Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        logger.error("Configuration error: {}", exc)
        raise SystemExit(1) from exc
    _log_settings(settings)
    return settings


@lru_cache
def load_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""

    try:
        settings = Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        logger.error("Configuration error: {}", exc)
        raise SystemExit(1) from exc
    _log_settings(settings)
    return settings


# Backwards compatible convenience instance.
class _SettingsProxy:
    """Lazily resolve settings to avoid eager validation.

    Importing modules that access :data:`settings` shouldn't require all
    environment variables to be present (e.g. ``cli --help``). This proxy
    defers loading until an attribute is accessed.
    """

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - simple delegation
        return getattr(load_settings(), name)

    def __setattr__(
        self, name: str, value: Any
    ) -> None:  # pragma: no cover - simple delegation
        setattr(load_settings(), name, value)


settings = _SettingsProxy()


__all__ = [
    "Settings",
    "settings",
    "load_settings",
    "load_env",
    "MODEL",
    "DEFAULT_MODEL_NAME",
]
