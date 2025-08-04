"""Tests for model configuration enforcement."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _stub_module(name: str, **attrs: object) -> None:
    module = types.ModuleType(name)
    module.__dict__.update(attrs)
    sys.modules[name] = module


def test_validate_model_configuration_rejects_override(monkeypatch, tmp_path):
    """``validate_model_configuration`` errors when MODEL_NAME is overridden."""

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-perplexity")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MODEL_NAME", "wrong-model")

    import config

    importlib.reload(config)

    # Provide a minimal package so ``from agentic_demo import config`` succeeds.
    pkg = types.ModuleType("agentic_demo")
    pkg.config = config
    sys.modules["agentic_demo"] = pkg
    sys.modules["agentic_demo.config"] = config

    def noop(*_args: object, **_kwargs: object) -> None:
        """No-op stub used to satisfy imports."""
        return None

    sg = types.SimpleNamespace(add_node=noop, add_edge=noop, add_conditional_edges=noop)
    _stub_module(
        "langgraph.graph",
        END=object(),
        START=object(),
        StateGraph=lambda *a, **k: sg,
    )
    _stub_module(
        "core.checkpoint",
        SqliteCheckpointManager=type(
            "CM",
            (),
            {"__init__": noop, "save_checkpoint": noop, "load_checkpoint": noop},
        ),
    )
    _stub_module("agents.approver", run_approver=noop)
    _stub_module("agents.content_weaver", run_content_weaver=noop)
    _stub_module(
        "agents.critics",
        run_fact_checker=noop,
        run_pedagogy_critic=noop,
    )
    _stub_module("agents.exporter", run_exporter=noop)
    _stub_module("agents.planner", PlanResult=object, run_planner=noop)
    _stub_module("agents.researcher_web_node", run_researcher_web=noop)
    _stub_module(
        "core.policies",
        policy_retry_on_critic_failure=lambda *a, **k: False,
        policy_retry_on_low_confidence=lambda *a, **k: False,
    )
    _stub_module("core.state", State=object)

    with pytest.raises(ValueError):
        import core.orchestrator as orchestrator

        importlib.reload(orchestrator)
