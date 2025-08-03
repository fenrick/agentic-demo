"""Tests for core.orchestrator module."""

from __future__ import annotations

from pathlib import Path

import pytest
from langgraph.graph import StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver

from agentic_demo.orchestration.state import State
from core import orchestrator


@pytest.fixture
def simple_graph() -> StateGraph:
    """Create a minimal graph for testing."""

    graph = StateGraph(State)
    graph.add_node("noop", lambda s: s)
    graph.set_entry_point("noop")
    graph.set_finish_point("noop")
    return graph


def test_compile_with_checkpoint_creates_db(
    simple_graph: StateGraph, tmp_path: Path
) -> None:
    """Function creates database and attaches saver."""

    compiled = orchestrator.compile_with_sqlite_checkpoint(simple_graph, tmp_path)
    assert (tmp_path / "checkpoint.db").exists()
    assert isinstance(compiled.checkpointer, SqliteSaver)


def test_compile_with_checkpoint_uses_settings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, simple_graph: StateGraph
) -> None:
    """DATA_DIR from settings is used when not provided."""

    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "p")
    monkeypatch.setenv("MODEL_NAME", "m")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    compiled = orchestrator.compile_with_sqlite_checkpoint(simple_graph)
    assert (tmp_path / "checkpoint.db").exists()
    assert isinstance(compiled.checkpointer, SqliteSaver)
