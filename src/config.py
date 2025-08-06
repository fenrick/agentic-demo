"""Application settings management.

Exposes configuration via a :class:`pydantic_settings.BaseSettings` subclass.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

try:  # pragma: no cover - optional dependency
    from dotenv import load_dotenv as _load_dotenv
except Exception:  # pragma: no cover - when python-dotenv is not installed

    def _load_dotenv(*_args: Any, **_kwargs: Any) -> bool:  # type: ignore[misc]
        """Fallback ``load_dotenv`` that does nothing when dependency missing."""
        return False


load_dotenv = _load_dotenv

# Load environment variables from a `.env` file if present.
load_dotenv()

# Default OpenAI model enforced across the application.
MODEL_NAME: str = "o4-mini"


class Settings(BaseSettings):
    """Configuration backed by environment variables.

    Only a subset of the original project's settings are implemented. Missing
    required variables raise a :class:`pydantic.ValidationError`.
    """

    openai_api_key: str
    perplexity_api_key: str
    data_dir: Path = Path("./workspace")
    tavily_api_key: str | None = None
    search_provider: str = "perplexity"
    model_name: str = MODEL_NAME
    offline_mode: bool = False
    enable_tracing: bool = True
    allowlist_domains: list[str] = ["wikipedia.org", ".edu", ".gov"]
    alert_webhook_url: str | None = None

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    @field_validator("data_dir", mode="before")
    @classmethod
    def _to_path(cls, value: str | Path) -> Path:
        return Path(value)

    @field_validator("allowlist_domains", mode="before")
    @classmethod
    def _parse_allowlist(cls, value: list[str] | str | None) -> list[str]:
        if value is None:
            return ["wikipedia.org", ".edu", ".gov"]
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError as exc:  # pragma: no cover - invalid input
                raise ValueError("ALLOWLIST_DOMAINS must be valid JSON") from exc
        return value


def load_env(env_file: Path) -> Settings:
    """Load :class:`Settings` from a specific ``.env`` file."""

    load_dotenv(env_file)
    return Settings()  # type: ignore[call-arg]


@lru_cache
def load_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""

    return Settings()  # type: ignore[call-arg]


# Backwards compatible convenience instance.
settings = load_settings()


__all__ = ["Settings", "settings", "load_settings", "load_env", "MODEL_NAME"]
