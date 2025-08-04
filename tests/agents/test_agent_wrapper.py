"""Tests for caching behavior in ``init_chat_model``."""

from __future__ import annotations

import os
import sys
import types

import pytest

# Ensure required environment variables so ``config`` loads during import.
os.environ.setdefault("OPENAI_API_KEY", "test-openai")
os.environ.setdefault("PERPLEXITY_API_KEY", "test-perplexity")
os.environ.setdefault("DATA_DIR", "/tmp")

import config

# Provide a minimal ``agentic_demo`` package for modules expecting it.
pkg = types.ModuleType("agentic_demo")
pkg.config = config
sys.modules["agentic_demo"] = pkg
sys.modules["agentic_demo.config"] = config

from agents import agent_wrapper as aw  # noqa: E402


def _stub_langchain(monkeypatch: pytest.MonkeyPatch, factory: object) -> None:
    """Provide a fake ``langchain_openai`` module with ``ChatOpenAI``."""

    module = types.SimpleNamespace(ChatOpenAI=factory)
    monkeypatch.setitem(sys.modules, "langchain_openai", module)


def test_init_chat_model_caches_instance(monkeypatch, tmp_path):
    """Repeated calls with same model name reuse the instance."""

    monkeypatch.setenv("OPENAI_API_KEY", "sk")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "pk")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    class FakeModel:
        pass

    def factory(**_kwargs):
        return FakeModel()

    _stub_langchain(monkeypatch, factory)

    aw.clear_model_cache()

    first = aw.init_chat_model()
    second = aw.init_chat_model()
    assert first is second


def test_clear_model_cache(monkeypatch, tmp_path):
    """Clearing the cache forces new model instantiation."""

    monkeypatch.setenv("OPENAI_API_KEY", "sk")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "pk")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    class FakeModel:
        pass

    def factory(**_kwargs):
        return FakeModel()

    _stub_langchain(monkeypatch, factory)

    aw.clear_model_cache()
    first = aw.init_chat_model()
    aw.clear_model_cache()
    second = aw.init_chat_model()
    assert first is not second
