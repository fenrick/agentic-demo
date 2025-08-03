"""Tests for the orchestration stubs."""

from __future__ import annotations

import pytest
from langgraph.graph import END, START

from core.orchestrator import (
    CitationResult,
    PlanResult,
    critic,
    graph,
    planner,
    researcher_web,
    writer,
)
from core.state import ActionLog, Citation, Outline, State


class OrchestratorState(State):
    """State extended with planner confidence for orchestrator tests."""

    confidence: float = 0.0


@pytest.mark.asyncio
async def test_planner_returns_plan_result() -> None:
    """Planner should echo outline and confidence from state."""
    state = OrchestratorState(outline=Outline(steps=["step"]), confidence=0.1)
    result = await planner(state)
    assert isinstance(result, PlanResult)
    assert result.outline == state.outline
    assert result.confidence == state.confidence


@pytest.mark.asyncio
async def test_researcher_web_returns_citation_results() -> None:
    """Researcher should wrap sources into citation results."""
    state = OrchestratorState(sources=[Citation(url="https://a")])
    results = await researcher_web(state)
    assert all(isinstance(r, CitationResult) for r in results)
    assert [r.url for r in results] == [s.url for s in state.sources]


@pytest.mark.asyncio
async def test_writer_echoes_state_and_critic_logs() -> None:
    """Writer returns the state and critic logs on success."""
    state = OrchestratorState(prompt="x")
    assert await writer(state) is state
    await critic(state)
    assert state.log == [ActionLog(message="critic")]


@pytest.mark.asyncio
async def test_critic_retries_until_success(monkeypatch) -> None:
    """Critic should retry transient failures up to three attempts."""
    calls = {"count": 0}

    async def flaky(state: OrchestratorState) -> float:
        calls["count"] += 1
        if calls["count"] < 3:
            raise RuntimeError("boom")
        return 0.9

    monkeypatch.setattr("core.orchestrator._evaluate", flaky)
    state = OrchestratorState()
    await critic(state)
    assert calls["count"] == 3
    assert state.log == [ActionLog(message="critic")]


@pytest.mark.asyncio
async def test_critic_raises_after_max_retries(monkeypatch) -> None:
    """Critic propagates error after exhausting retries without side effects."""

    async def always_fail(state: OrchestratorState) -> float:
        raise RuntimeError("boom")

    monkeypatch.setattr("core.orchestrator._evaluate", always_fail)
    state = OrchestratorState()
    with pytest.raises(RuntimeError):
        await critic(state)
    assert state.log == []


def test_graph_structure() -> None:
    """Graph wires planner-researcher loop with writer and critic tail."""
    nodes = set(graph.nodes.keys())
    assert {"Planner", "Researcher", "Writer", "Critic"}.issubset(nodes)
    assert (START, "Planner") in graph.edges
    assert ("Researcher", "Planner") in graph.edges
    assert ("Writer", "Critic") in graph.edges
    assert ("Critic", END) in graph.edges
    branch = graph.branches["Planner"]["planner_router"].ends
    assert branch == {"research": "Researcher", "write": "Writer"}
