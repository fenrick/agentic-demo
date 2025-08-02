"""Tests for the :mod:`agentic_demo.config` module."""

from pathlib import Path

import pytest

from agentic_demo.config import load_env


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
    with pytest.raises(KeyError):
        load_env(file)


def test_env_vars_override_env_file(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Environment variables take precedence over `.env` values."""

    monkeypatch.setenv("MODEL_NAME", "override-model")
    monkeypatch.setenv("OPENAI_API_KEY", "override-openai")
    config = load_env(env_file)
    assert config.model_name == "override-model"
    assert config.openai_api_key == "override-openai"
