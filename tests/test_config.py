"""Tests for the :mod:`agentic_demo.config` module."""

from pathlib import Path

import pytest

from agentic_demo.config import load_env


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


def test_load_env_returns_config(env_file: Path) -> None:
    """``load_env`` parses values from the `.env` file."""
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


def test_environment_overrides_file(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Environment variables override `.env` values."""
    monkeypatch.setenv("MODEL_NAME", "override-model")
    config = load_env(env_file)
    assert config.model_name == "override-model"
