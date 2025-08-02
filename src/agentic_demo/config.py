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

    OPENAI_API_KEY: str = Field(..., description="API key for OpenAI services.")
    PERPLEXITY_API_KEY: str = Field(..., description="API key for Perplexity services.")
    MODEL_NAME: str = Field(..., description="Default model identifier to use.")
    DATA_DIR: Path = Field(..., description="Directory for application data.")
    OFFLINE_MODE: bool = Field(
        False, description="Run application without external network calls."
    )

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=True)
