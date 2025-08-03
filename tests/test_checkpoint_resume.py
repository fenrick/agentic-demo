"""Integration test for graph checkpoint resumption."""

from importlib import reload
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from agents.planner import PlanResult
from core.state import State


@pytest.mark.asyncio
async def test_checkpoint_resume(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Orchestrator should persist state and resume from SQLite checkpoint."""
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "y")
    monkeypatch.setenv("MODEL_NAME", "m")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    import core.orchestrator as orchestrator

    reload(orchestrator)

    await orchestrator.graph_orchestrator.start("orig")
    db_path = tmp_path / "checkpoint.db"
    assert db_path.exists()

    seen: dict[str, str] = {}

    async def fake_planner(state: State) -> PlanResult:
        seen["prompt"] = state.prompt
        return PlanResult()

    monkeypatch.setattr("agents.planner.run_planner", fake_planner)

    await orchestrator.graph_orchestrator.resume()
    assert seen["prompt"] == "orig"
