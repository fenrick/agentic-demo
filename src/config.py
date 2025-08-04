"""Application settings management.

Exposes configuration via a :class:`pydantic_settings.BaseSettings` subclass.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from a `.env` file if present.
load_dotenv()

# Default OpenAI model enforced across the application.
MODEL_NAME: str = "o4-mini"


class Settings(BaseSettings):
    """Strongly-typed application configuration.

    Purpose:
        Provide access to environment-driven settings for the application.

    Inputs:
        Values are sourced from environment variables or an ``.env`` file.

    Outputs:
        Instances expose the parsed configuration fields as attributes.

    Side Effects:
        On import, :func:`dotenv.load_dotenv` loads variables from ``.env`` into
        :mod:`os.environ` if the file exists.

    Exceptions:
        :class:`pydantic.ValidationError` is raised if required variables are
        missing or invalid.
    """

    openai_api_key: str = Field(
        ..., alias="OPENAI_API_KEY", description="API key for OpenAI services."
    )
    perplexity_api_key: str = Field(
        ..., alias="PERPLEXITY_API_KEY", description="API key for Perplexity services."
    )
    tavily_api_key: str | None = Field(
        None, alias="TAVILY_API_KEY", description="API key for Tavily search."
    )
    search_provider: Literal["perplexity", "tavily"] = Field(
        "perplexity",
        alias="SEARCH_PROVIDER",
        description="Web search provider to use.",
    )
    model_name: str = Field(
        MODEL_NAME,
        alias="MODEL_NAME",
        description="Default model identifier to use.",
    )
    data_dir: Path = Field(
        ..., alias="DATA_DIR", description="Directory for application data."
    )
    offline_mode: bool = Field(
        False,
        alias="OFFLINE_MODE",
        description="Run application without external network calls.",
    )
    allowlist_domains: List[str] = Field(
        default_factory=lambda: ["wikipedia.org", ".edu", ".gov"],
        alias="ALLOWLIST_DOMAINS",
        description="Domain patterns permitted for citation use.",
    )
    alert_webhook_url: str | None = Field(
        None,
        alias="ALERT_WEBHOOK_URL",
        description="Webhook endpoint for threshold breach alerts.",
    )

    model_config = SettingsConfigDict(
        env_prefix="", case_sensitive=True, populate_by_name=True
    )


def load_env(env_file: Path) -> Settings:
    """Load :class:`Settings` from a specific ``.env`` file."""

    load_dotenv(env_file)
    return Settings(_env_file=env_file)  # type: ignore[call-arg]


_settings: Settings | None = None


def load_settings() -> Settings:
    """Return a singleton :class:`Settings` instance.

    The configuration values are pulled from environment variables and validated
    by :class:`Settings`. Subsequent calls return the cached instance.
    """

    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings


# Eagerly instantiate settings for modules that import it directly.
settings = load_settings()

__all__ = ["Settings", "load_settings", "load_env", "settings", "MODEL_NAME"]
