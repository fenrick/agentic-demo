"""Orchestration graph stubs built on LangGraph."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import List

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agentic_demo.config import Settings

from .state import Outline, State

try:  # pragma: no cover - import path varies with package version
    from langgraph_checkpoint_sqlite import SqliteCheckpointSaver  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from langgraph.checkpoint.sqlite import SqliteSaver as SqliteCheckpointSaver


@dataclass(slots=True)
class PlanResult:
    """Placeholder plan result produced by the planner.

    Attributes:
        outline: Proposed outline for the document.
    """

    outline: Outline | None


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

    TODO: Replace with actual planning algorithm.

    Args:
        state: The evolving orchestration state.

    Returns:
        PlanResult echoing the state's outline.
    """

    return PlanResult(outline=state.outline)


async def researcher_web(state: State) -> List[CitationResult]:
    """Collect citations from the web.

    TODO: Implement real web retrieval and citation scoring.

    Args:
        state: The evolving orchestration state containing source hints.

    Returns:
        List of :class:`CitationResult` mirroring provided sources.
    """

    return [CitationResult(url=src.url, title=src.url) for src in state.sources]


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
        state: Current state carrying collected sources.

    Returns:
        ``"research"`` to loop back or ``"write"`` when sources exist.
    """

    return "write" if state.sources else "research"


graph.add_conditional_edges(
    "Planner", planner_router, {"research": "Researcher", "write": "Writer"}
)

graph.add_edge("Researcher", "Planner")
graph.add_edge("Writer", "Critic")
graph.add_edge("Critic", END)


# TODO: Handle alternative checkpoint backends beyond SQLite.


def compile_with_sqlite_checkpoint(
    graph: StateGraph, data_dir: Path | None = None
) -> CompiledStateGraph:
    """Compile ``graph`` with SQLite-backed checkpointing.

    Purpose:
        Ensure graphs persist state between runs using a SQLite checkpoint saver.

    Inputs:
        graph: StateGraph to compile.
        data_dir: Optional directory for database storage. Defaults to ``Settings.DATA_DIR``.

    Outputs:
        Compiled graph configured with a SQLite checkpoint saver.

    Side Effects:
        Creates ``data_dir`` and a ``checkpoint.db`` file if absent.

    Exceptions:
        Propagates from file system access or graph compilation.
    """

    data_dir = data_dir or Settings().data_dir  # type: ignore[call-arg]
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "checkpoint.db"

    try:
        saver = SqliteCheckpointSaver(path=str(db_path))  # type: ignore[arg-type]
    except TypeError:  # pragma: no cover - fallback for older API
        conn = sqlite3.connect(db_path, check_same_thread=False)
        saver = SqliteCheckpointSaver(conn)  # type: ignore[arg-type]

    return graph.compile(checkpointer=saver)
