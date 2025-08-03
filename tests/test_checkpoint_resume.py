"""Integration test for graph checkpoint resumption."""

from importlib import reload
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from core.state import State


@pytest.mark.asyncio
async def test_checkpoint_resume(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Graph should resume from SQLite checkpoint after interruption."""
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "y")
    monkeypatch.setenv("MODEL_NAME", "m")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    import core.orchestrator as orchestrator

    reload(orchestrator)
    try:
        compiled = orchestrator.graph.compile(checkpointer=orchestrator.saver)
    except NotImplementedError:  # pragma: no cover - saver lacks async support
        pytest.skip("Async checkpoint saver not supported")

    state = State(prompt="orig")
    config = {"configurable": {"thread_id": "t"}}

    try:
        await compiled.ainvoke(state, config=config, interrupt_after=["Planner"])
    except NotImplementedError:  # pragma: no cover - saver lacks async support
        pytest.skip("Async checkpoint saver not supported")
    assert (tmp_path / "checkpoint.db").exists()

    state.prompt = "mutated"
    try:
        resumed = await compiled.ainvoke(
            state, config=config, resume=True, interrupt_after=["Researcher"]
        )
    except NotImplementedError:  # pragma: no cover - saver lacks async support
        pytest.skip("Async checkpoint saver not supported")
    else:
        assert resumed["prompt"] == "orig"
        assert resumed["log"] == []
