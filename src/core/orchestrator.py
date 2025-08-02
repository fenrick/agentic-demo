"""Orchestration graph stubs built on LangGraph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from langgraph.graph import END, START, StateGraph

from agentic_demo.orchestration.state import State


@dataclass(slots=True)
class PlanResult:
    """Placeholder plan result produced by the planner.

    Attributes:
        outline: Proposed outline for the document.
        confidence: Planner's confidence score.
    """

    outline: List[str]
    confidence: float


@dataclass(slots=True)
class CitationResult:
    """Simplified citation container for web research results.

    Attributes:
        url: Source URL.
        title: Short human readable title.
    """

    url: str
    title: str


async def planner(state: State) -> PlanResult:
    """Draft a plan from the current state.

    TODO: Replace with actual LLM-powered planning.

    Args:
        state: The evolving orchestration state.

    Returns:
        PlanResult echoing the state's outline and confidence.
    """

    return PlanResult(outline=state.outline, confidence=state.confidence)


async def researcher_web(state: State) -> List[CitationResult]:
    """Collect citations from the web.

    TODO: Implement real web retrieval and citation scoring.

    Args:
        state: The evolving orchestration state containing source hints.

    Returns:
        List of :class:`CitationResult` mirroring provided sources.
    """

    return [CitationResult(url=src, title=src) for src in state.sources]


async def writer(state: State) -> State:
    """Placeholder writer node.

    TODO: Weave researched content into final narrative.

    Args:
        state: The evolving orchestration state.

    Returns:
        Unmodified state for now.
    """

    return state


async def critic(state: State) -> State:
    """Placeholder critic node.

    TODO: Evaluate drafted content for quality and consistency.

    Args:
        state: The evolving orchestration state.

    Returns:
        Unmodified state for now.
    """

    return state


graph = StateGraph(State)
graph.add_node("Planner", planner, streams="values")  # type: ignore[arg-type, call-overload]
graph.add_node(
    "Researcher", researcher_web, streams="updates"
)  # type: ignore[arg-type, call-overload]
graph.add_node("Writer", writer, streams="values")  # type: ignore[arg-type, call-overload]
graph.add_node("Critic", critic, streams="values")  # type: ignore[arg-type, call-overload]
graph.add_edge(START, "Planner")


def planner_router(state: State) -> str:
    """Decide whether more research is required.

    Args:
        state: Current state carrying planner confidence.

    Returns:
        ``"research"`` to loop back or ``"write"`` when confident.
    """

    return "research" if state.confidence < 0.9 else "write"


graph.add_conditional_edges(
    "Planner", planner_router, {"research": "Researcher", "write": "Writer"}
)
graph.add_edge("Researcher", "Planner")
graph.add_edge("Writer", "Critic")
graph.add_edge("Critic", END)
