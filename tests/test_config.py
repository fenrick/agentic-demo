"""Tests for the :mod:`agentic_demo.config` module."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from agentic_demo import config


def _write_env(tmp_path: Path) -> Path:
    """Create a `.env` file with all required keys."""

    content = (
        "OPENAI_API_KEY=sk-123\n"
        "PERPLEXITY_API_KEY=pp-456\n"
        "MODEL_NAME=gpt-4o\n"
        "DATA_DIR=/data\n"
    )
    file = tmp_path / ".env"
    file.write_text(content)
    return file


def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove configuration variables from the environment."""

    for key in [
        "OPENAI_API_KEY",
        "PERPLEXITY_API_KEY",
        "MODEL_NAME",
        "DATA_DIR",
        "OFFLINE_MODE",
    ]:
        monkeypatch.delenv(key, raising=False)


def test_settings_loads_from_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``Settings`` loads variables from a `.env` file automatically."""

    _write_env(tmp_path)
    _clear_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    importlib.reload(config)
    settings = config.Settings()
    assert settings.OPENAI_API_KEY == "sk-123"
    assert settings.PERPLEXITY_API_KEY == "pp-456"
    assert settings.MODEL_NAME == "gpt-4o"
    assert settings.DATA_DIR == Path("/data")
    assert settings.OFFLINE_MODE is False


def test_missing_key_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Validation fails when a required key is absent."""

    file = tmp_path / ".env"
    file.write_text("OPENAI_API_KEY=sk-123\n")
    _clear_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    importlib.reload(config)
    with pytest.raises(ValidationError):
        config.Settings()


def test_environment_overrides_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Environment variables override values from `.env`."""

    _write_env(tmp_path)
    _clear_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    importlib.reload(config)
    monkeypatch.setenv("MODEL_NAME", "override-model")
    settings = config.Settings()
    assert settings.MODEL_NAME == "override-model"
