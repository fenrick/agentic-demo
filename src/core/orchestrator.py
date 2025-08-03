"""Orchestration graph stubs built on LangGraph."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from pathlib import Path
from typing import List

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agentic_demo.config import Settings
from core.state import State


@dataclass(slots=True)
class PlanResult:
    """Placeholder plan result produced by the planner.

    Attributes:
        outline: Proposed outline for the document.
    """

    outline: List[str]


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

    Args:
        state: The evolving orchestration state.

    Returns:
        PlanResult echoing the state's outline.
    """

    steps = state.outline.steps if state.outline else []
    return PlanResult(outline=steps)


async def researcher_web(state: State) -> List[CitationResult]:
    """Collect citations from the web.

    Args:
        state: The evolving orchestration state containing source hints.

    Returns:
        List of :class:`CitationResult` mirroring provided sources.
    """

    return [CitationResult(url=src.url, title=src.url) for src in state.sources]


async def writer(state: State) -> State:
    """Placeholder writer node."""

    return state


async def critic(state: State) -> State:
    """Placeholder critic node."""

    return state


# Build orchestration graph
graph = StateGraph(State)
graph.add_node("Planner", planner, streams="values")  # type: ignore[arg-type, call-overload]
graph.add_node("Researcher", researcher_web, streams="updates")  # type: ignore[arg-type, call-overload]
graph.add_node("Writer", writer, streams="values")  # type: ignore[arg-type, call-overload]
graph.add_node("Critic", critic, streams="values")  # type: ignore[arg-type, call-overload]
graph.add_edge(START, "Planner")


def planner_router(state: State) -> str:
    """Decide whether more research is required."""

    return "research" if not state.sources else "write"


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

    Args:
        graph: StateGraph to compile.
        data_dir: Optional directory for database storage. Defaults to ``Settings.DATA_DIR``.

    Returns:
        Compiled graph configured with a SQLite checkpoint saver.
    """

    data_dir = data_dir or Settings().data_dir  # type: ignore[attr-defined, call-arg]
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "checkpoint.db"

    try:
        from langgraph_checkpoint_sqlite import SqliteCheckpointSaver  # type: ignore

        saver = SqliteCheckpointSaver(path=str(db_path))  # type: ignore[arg-type]
    except ModuleNotFoundError:  # pragma: no cover
        from langgraph.checkpoint.sqlite import SqliteSaver as SqliteCheckpointSaver

        conn = sqlite3.connect(db_path, check_same_thread=False)
        saver = SqliteCheckpointSaver(conn)  # type: ignore[arg-type]
    except TypeError:  # pragma: no cover - fallback for older API
        from langgraph.checkpoint.sqlite import SqliteSaver as SqliteCheckpointSaver

        conn = sqlite3.connect(db_path, check_same_thread=False)
        saver = SqliteCheckpointSaver(conn)  # type: ignore[arg-type]

    return graph.compile(checkpointer=saver)
