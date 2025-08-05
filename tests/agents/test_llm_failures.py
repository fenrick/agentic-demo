"""Tests for LLM failure handling and logging."""

import logging
import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Provide minimal configuration so modules importing ``agentic_demo`` succeed.
os.environ.setdefault("OPENAI_API_KEY", "test-openai")
os.environ.setdefault("PERPLEXITY_API_KEY", "test-perplexity")
os.environ.setdefault("DATA_DIR", "/tmp")

config = types.SimpleNamespace(
    settings=types.SimpleNamespace(model_name="gpt-4", perplexity_api_key="pk")
)

pkg = types.ModuleType("agentic_demo")
pkg.config = config
sys.modules["agentic_demo"] = pkg
sys.modules["agentic_demo.config"] = config

core_pkg = types.ModuleType("core")
core_state = types.ModuleType("core.state")
core_state.State = type("State", (), {})
core_pkg.state = core_state
sys.modules["core"] = core_pkg
sys.modules["core.state"] = core_state

sys.modules["prompts"] = types.SimpleNamespace(get_prompt=lambda *_args, **_kwargs: "")

from agents import agent_wrapper  # noqa: E402
from agents.pedagogy_critic import classify_bloom_level  # noqa: E402


def test_init_chat_model_logs_on_failure(monkeypatch, caplog):
    """Chat model initialization failures are logged and return ``None``."""

    class DummyChat:
        def __init__(self, *args, **kwargs):  # pragma: no cover - test stub
            raise RuntimeError("boom")

    monkeypatch.setitem(
        sys.modules, "langchain_openai", SimpleNamespace(ChatOpenAI=DummyChat)
    )
    agent_wrapper.clear_model_cache()
    caplog.set_level(logging.ERROR)

    model = agent_wrapper.init_chat_model(model="gpt-4")

    assert model is None
    assert "Failed to initialize chat model" in caplog.text


def test_classify_bloom_level_logs_and_falls_back(monkeypatch, caplog):
    """Classification falls back and logs when the LLM raises an error."""

    class FailingModel:
        def invoke(self, _prompt):  # pragma: no cover - test stub
            raise RuntimeError("fail")

    monkeypatch.setattr(
        "agents.pedagogy_critic.init_chat_model", lambda: FailingModel()
    )
    caplog.set_level(logging.ERROR)

    level = classify_bloom_level("list the items")

    assert level == "remember"  # falls back to keyword classifier
    assert "Bloom level classification failed" in caplog.text
