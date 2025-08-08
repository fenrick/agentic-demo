from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsError

from config import Settings, load_env


def test_settings_loads_env(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "key1")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "key2")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings = Settings()
    assert settings.openai_api_key == "key1"
    assert settings.perplexity_api_key == "key2"
    assert settings.data_dir == tmp_path


def test_settings_missing_required(monkeypatch):
    for name in ["OPENAI_API_KEY", "PERPLEXITY_API_KEY"]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("DATA_DIR", raising=False)
    with pytest.raises(ValidationError):
        Settings()


def test_settings_uses_default_data_dir(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "key1")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "key2")
    monkeypatch.delenv("DATA_DIR", raising=False)
    settings = Settings()
    assert settings.data_dir == Path("./workspace")


def test_settings_parses_allowlist_json(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "key1")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "key2")
    monkeypatch.setenv("ALLOWLIST_DOMAINS", '["example.com"]')
    settings = Settings()
    assert settings.allowlist_domains == ["example.com"]


def test_settings_rejects_invalid_allowlist(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "key1")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "key2")
    monkeypatch.setenv("ALLOWLIST_DOMAINS", "not-json")
    with pytest.raises(SettingsError):
        Settings()


def test_settings_defaults_allowlist(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "key1")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "key2")
    monkeypatch.delenv("ALLOWLIST_DOMAINS", raising=False)
    settings = Settings()
    assert settings.allowlist_domains == ["wikipedia.org", ".edu", ".gov"]


def test_load_env_reads_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=a\nPERPLEXITY_API_KEY=b\nDATA_DIR=/tmp\n")
    settings = load_env(env_file)
    assert settings.openai_api_key == "a"
    assert settings.perplexity_api_key == "b"
    assert settings.data_dir == Path("/tmp")
