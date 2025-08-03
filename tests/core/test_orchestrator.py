"""Tests for the orchestration stubs."""

from __future__ import annotations

import pytest
from langgraph.graph import END, START

from core.state import Citation, Outline, State
from core.orchestrator import (
    CitationResult,
    PlanResult,
    critic,
    graph,
    planner,
    researcher_web,
    writer,
)


@pytest.mark.asyncio
async def test_planner_returns_plan_result() -> None:
    """Planner should echo outline from state."""
    state = State(outline=Outline(steps=["step"]))
    result = await planner(state)
    assert isinstance(result, PlanResult)
    assert result.outline == ["step"]


@pytest.mark.asyncio
async def test_researcher_web_returns_citation_results() -> None:
    """Researcher should wrap sources into citation results."""
    state = State(sources=[Citation(url="https://a")])
    results = await researcher_web(state)
    assert all(isinstance(r, CitationResult) for r in results)
    assert [r.url for r in results] == [c.url for c in state.sources]


@pytest.mark.asyncio
async def test_placeholder_nodes_echo_state() -> None:
    """Writer and critic currently return the state unchanged."""
    state = State(prompt="x")
    assert await writer(state) is state
    assert await critic(state) is state


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
