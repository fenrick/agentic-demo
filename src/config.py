"""Application settings management.

Exposes configuration via a :class:`pydantic_settings.BaseSettings` subclass.
"""

from __future__ import annotations

from pathlib import Path

import json
import os

try:  # pragma: no cover - optional dependency
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - when python-dotenv is not installed

    def load_dotenv(*_args, **_kwargs):  # type: ignore[override]
        """Fallback ``load_dotenv`` that does nothing when dependency missing."""
        return False


from pydantic import ValidationError  # provided by a lightweight stub in tests

# Load environment variables from a `.env` file if present.
load_dotenv()

# Default OpenAI model enforced across the application.
MODEL_NAME: str = "o4-mini"


class Settings:
    """Lightweight settings loader used in tests.

    Only a very small subset of the original project's configuration system is
    implemented.  Environment variables are read directly and minimal
    validation is performed.  Missing required variables raise a
    :class:`pydantic.ValidationError` to mirror the behaviour expected by the
    tests.
    """

    def __init__(self, _env_file: Path | None = None) -> None:
        if _env_file is not None:
            load_dotenv(_env_file)

        def _req(name: str) -> str:
            value = os.getenv(name)
            if not value:
                raise ValidationError(f"Missing environment variable: {name}")
            return value

        self.openai_api_key = _req("OPENAI_API_KEY")
        self.perplexity_api_key = _req("PERPLEXITY_API_KEY")
        self.data_dir = Path(_req("DATA_DIR"))

        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.search_provider = os.getenv("SEARCH_PROVIDER", "perplexity")
        self.model_name = os.getenv("MODEL_NAME", MODEL_NAME)
        self.offline_mode = os.getenv("OFFLINE_MODE", "false").lower() == "true"
        # Toggle for OpenTelemetry instrumentation. Modules are always imported
        # but instrumentation can be disabled via configuration.
        self.enable_tracing = os.getenv("ENABLE_TRACING", "true").lower() == "true"
        allowlist_raw = os.getenv("ALLOWLIST_DOMAINS")
        if allowlist_raw:
            try:
                self.allowlist_domains = json.loads(allowlist_raw)
            except json.JSONDecodeError as exc:  # pragma: no cover - invalid input
                raise ValidationError("ALLOWLIST_DOMAINS must be valid JSON") from exc
        else:
            self.allowlist_domains = ["wikipedia.org", ".edu", ".gov"]
        self.alert_webhook_url = os.getenv("ALERT_WEBHOOK_URL")


def load_env(env_file: Path) -> Settings:
    """Load :class:`Settings` from a specific ``.env`` file."""

    load_dotenv(env_file)
    return Settings()


_settings: Settings | None = None


def load_settings() -> Settings:
    """Return a singleton :class:`Settings` instance."""

    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# ``settings`` is populated lazily by :func:`load_settings` so that importing
# this module does not require environment variables to be preset.  Callers may
# explicitly invoke :func:`load_settings` or instantiate :class:`Settings`
# directly.
settings: Settings | None = None

__all__ = ["Settings", "load_settings", "load_env", "settings", "MODEL_NAME"]
