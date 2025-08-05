"""Validation tests for the application configuration."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

# Provide default values so ``agentic_demo.config`` can import successfully.
os.environ.setdefault("OPENAI_API_KEY", "placeholder-openai")
os.environ.setdefault("PERPLEXITY_API_KEY", "placeholder-perplexity")
os.environ.setdefault("DATA_DIR", "/tmp")

import config  # noqa: E402

# Required configuration values for the application.
REQUIRED_ENV = {
    "OPENAI_API_KEY": "sk-123",
    "PERPLEXITY_API_KEY": "pp-456",
    "DATA_DIR": "/data",
}


@pytest.fixture(autouse=True)
def clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove configuration keys from the environment before each test."""

    for key in REQUIRED_ENV:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)


def test_settings_loads_with_required_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """``Settings`` initializes when all required keys are present."""

    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)

    settings = config.Settings()
    assert settings.perplexity_api_key == REQUIRED_ENV["PERPLEXITY_API_KEY"]
    assert settings.data_dir == Path(REQUIRED_ENV["DATA_DIR"])


@pytest.mark.parametrize("missing_key", REQUIRED_ENV.keys())
def test_missing_required_key_raises(
    monkeypatch: pytest.MonkeyPatch, missing_key: str
) -> None:
    """Validation fails if any required key is absent."""

    for key, value in REQUIRED_ENV.items():
        if key != missing_key:
            monkeypatch.setenv(key, value)

    with pytest.raises(ValidationError):
        config.Settings()
