"""Application settings management.

Exposes configuration via a :class:`pydantic_settings.BaseSettings` subclass.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from a `.env` file if present.
load_dotenv()


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
    model_name: str = Field(
        ..., alias="MODEL_NAME", description="Default model identifier to use."
    )
    data_dir: Path = Field(
        ..., alias="DATA_DIR", description="Directory for application data."
    )
    offline_mode: bool = Field(
        False,
        alias="OFFLINE_MODE",
        description="Run application without external network calls.",
    )

    model_config = SettingsConfigDict(
        env_prefix="", case_sensitive=True, populate_by_name=True
    )


def load_env(env_file: Path) -> Settings:
    """Load :class:`Settings` from a specific ``.env`` file."""

    load_dotenv(env_file)
    return Settings(_env_file=env_file)  # type: ignore[call-arg]
