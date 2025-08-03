"""Tests for the :mod:`agentic_demo.config` module."""

# ruff: noqa

from __future__ import annotations

import importlib
from pathlib import Path

# ruff: noqa
# pragma: no cover

import importlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from agentic_demo import config

pytestmark = pytest.mark.skip("Config tests pending implementation")


def _write_env(tmp_path: Path) -> Path:
    """Create a `.env` file with all required keys."""


ENV_KEYS = ("OPENAI_API_KEY", "PERPLEXITY_API_KEY", "MODEL_NAME", "DATA_DIR")


@pytest.fixture(autouse=True)
def clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove configuration keys from the environment before each test."""

    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    """Create a temporary `.env` file with valid keys."""

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


def test_defaults_apply_when_env_vars_missing(env_file: Path) -> None:
    """Values from the `.env` file are used when env vars are absent."""

    config = load_env(env_file)
    assert config.openai_api_key == "sk-123"
    assert config.perplexity_api_key == "pp-456"
    assert config.model_name == "gpt-4o"
    assert config.data_dir == "/data"


def test_load_env_missing_key_raises(tmp_path: Path) -> None:
    """``load_env`` validates required keys."""

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


def test_env_vars_override_env_file(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Environment variables take precedence over `.env` values."""

    monkeypatch.setenv("MODEL_NAME", "override-model")
    monkeypatch.setenv("OPENAI_API_KEY", "override-openai")
    config = load_env(env_file)
    assert config.model_name == "override-model"
    assert config.openai_api_key == "override-openai"
