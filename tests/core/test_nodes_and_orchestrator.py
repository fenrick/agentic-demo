"""Tests for node handlers and orchestrator wiring."""

from __future__ import annotations

import pytest
from langgraph.graph import END, START

from core.nodes.planner import PlanResult, run_planner
from core.nodes.researcher_web import run_researcher_web
from core.orchestrator import GraphOrchestrator
from core.state import Citation, Outline, State
from web.researcher_web import CitationResult


class OrchestratorState(State):
    """State extended with planner confidence for testing."""

    confidence: float = 0.0


@pytest.mark.asyncio
async def test_run_planner_returns_plan_result() -> None:
    """Planner should echo outline in the result."""
    state = OrchestratorState(outline=Outline(steps=["step"]))
    result = await run_planner(state)
    assert isinstance(result, PlanResult)
    assert result.outline == state.outline


@pytest.mark.asyncio
async def test_run_researcher_web_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Researcher node should delegate to web helper."""
    seen: list[list[str]] = []

    async def fake_helper(urls: list[str]) -> list[CitationResult]:
        seen.append(urls)
        return [CitationResult(url=u, content="") for u in urls]

    monkeypatch.setattr("core.nodes.researcher_web.researcher_web", fake_helper)

    state = OrchestratorState(
        sources=[Citation(url="https://a"), Citation(url="https://b")]
    )
    results = await run_researcher_web(state)
    assert seen == [["https://a", "https://b"]]
    assert [r.url for r in results] == ["https://a", "https://b"]


def test_orchestrator_wires_graph() -> None:
    """GraphOrchestrator should register nodes and edges correctly."""
    orchestrator = GraphOrchestrator()
    orchestrator.initialize_graph()
    orchestrator.register_edges()
    graph = orchestrator.graph
    assert graph is not None
    nodes = set(graph.nodes.keys())
    assert {
        "Planner",
        "Researcher-Web",
        "Content-Weaver",
        "Pedagogy-Critic",
        "Fact-Checker",
        "Human-In-Loop",
        "Exporter",
    }.issubset(nodes)
    assert (START, "Planner") in graph.edges
    assert ("Planner", "Researcher-Web") in graph.edges
    assert ("Planner", "Content-Weaver") in graph.edges
    assert ("Researcher-Web", "Planner") in graph.edges
    assert ("Human-In-Loop", "Exporter") in graph.edges
    assert ("Exporter", END) in graph.edges


@pytest.mark.asyncio
async def test_start_invokes_planner(monkeypatch: pytest.MonkeyPatch) -> None:
    """Starting the orchestrator should call the planner."""
    called: dict[str, str] = {}

    async def fake_planner(state: State) -> PlanResult:
        called["prompt"] = state.prompt
        return PlanResult()

    monkeypatch.setattr("core.nodes.planner.run_planner", fake_planner)
    orchestrator = GraphOrchestrator()
    result = await orchestrator.start("hello")
    assert called["prompt"] == "hello"
    assert isinstance(result, PlanResult)
