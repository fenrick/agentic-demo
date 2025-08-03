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
    planner_router,
    researcher_web,
    writer,
)


@pytest.mark.asyncio
async def test_planner_returns_plan_result() -> None:
    """Planner should echo outline from state."""
    outline = Outline(steps=["step"])
    state = State(outline=outline)
    result = await planner(state)
    assert isinstance(result, PlanResult)
    assert result.outline == state.outline


@pytest.mark.asyncio
async def test_researcher_web_returns_citation_results() -> None:
    """Researcher should wrap sources into citation results."""
    citation = Citation(url="https://a")
    state = State(sources=[citation])
    results = await researcher_web(state)
    assert all(isinstance(r, CitationResult) for r in results)
    assert [r.url for r in results] == [citation.url]


@pytest.mark.asyncio
async def test_placeholder_nodes_echo_state() -> None:
    """Writer and critic currently return the state unchanged."""
    state = State(prompt="x")
    assert await writer(state) is state
    assert await critic(state) is state


def test_graph_structure() -> None:
    """Graph wires planner-researcher loop with writer and critic tail."""
    nodes = graph.nodes
    assert {"Planner", "Researcher", "Writer", "Critic"}.issubset(nodes.keys())
    assert (START, "Planner") in graph.edges
    assert ("Researcher", "Planner") in graph.edges
    assert ("Writer", "Critic") in graph.edges
    assert ("Critic", END) in graph.edges
    branch = graph.branches["Planner"]["planner_router"].ends
    assert branch == {"research": "Researcher", "write": "Writer"}


def test_planner_router_policy() -> None:
    """Router sends states with sources to writer else researcher."""
    assert planner_router(State()) == "research"
    assert planner_router(State(sources=[Citation(url="a")])) == "write"
