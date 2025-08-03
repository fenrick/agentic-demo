"""LangGraph-based orchestration stubs.

This module wires together placeholder nodes using :class:`langgraph.graph.StateGraph`.
Each node is intentionally minimal and will be expanded with real logic in future
iterations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import List

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from tenacity import retry, stop_after_attempt

from agentic_demo.config import Settings
from core.state import ActionLog, Outline, State
from web.researcher_web import CitationResult, researcher_web as _web_research

try:  # pragma: no cover - import path varies with package version
    from langgraph_checkpoint_sqlite import SqliteCheckpointSaver  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from langgraph.checkpoint.sqlite import SqliteSaver as SqliteCheckpointSaver


@dataclass(slots=True)
class PlanResult:
    """Output of the planner node.

    Attributes:
        outline: Proposed structure for downstream processing.
        confidence: Heuristic confidence score in the plan.
    """

    outline: Outline | None = None
    confidence: float = 0.0


async def planner(state: State) -> PlanResult:
    """Draft a plan from the current state.

    Purpose:
        Prepare an outline and confidence score for guiding further steps.

    Inputs:
        state: Current :class:`State` of the run.

    Outputs:
        :class:`PlanResult` containing the state's outline and confidence.

    Side Effects:
        None.

    Exceptions:
        None.
    """

    outline = state.outline
    confidence = getattr(state, "confidence", 0.0)
    return PlanResult(outline=outline, confidence=confidence)


async def researcher_web(state: State) -> List[CitationResult]:
    """Collect citations from the web concurrently and deduplicate them.

    Purpose:
        Fetch external information sources based on URLs in ``state.sources``.

    Inputs:
        state: Current :class:`State` whose ``sources`` provide seed URLs.

    Outputs:
        List of :class:`CitationResult` objects from unique domains.

    Side Effects:
        Performs network I/O via the helper in :mod:`web.researcher_web`.

    Exceptions:
        Propagated from the underlying fetches after helper-level handling.
    """

    urls = [c.url for c in state.sources]
    return await _web_research(urls)


async def writer(state: State) -> State:
    """Placeholder writer node.

    Currently returns the ``state`` unchanged.
    """

    return state


async def _evaluate(state: State) -> float:  # pragma: no cover - patched in tests
    """Return a dummy quality score."""

    return 1.0


@retry(stop=stop_after_attempt(3), reraise=True)
async def critic(state: State) -> State:
    """Evaluate content quality with retry on transient errors.

    Purpose:
        Append a log entry indicating the critic ran successfully.

    Inputs:
        state: Current :class:`State` of the run.

    Outputs:
        The same ``state`` with a new ``ActionLog`` entry.

    Side Effects:
        Mutates ``state.log`` on success.

    Exceptions:
        Propagates the last exception from ``_evaluate`` after exhausting retries.
    """

    await _evaluate(state)
    state.log.append(ActionLog(message="critic"))
    return state


# Build orchestration graph
graph = StateGraph(State)
graph.add_node("Planner", planner, streams="values")  # type: ignore[arg-type, call-overload]
graph.add_node("Researcher", researcher_web, streams="updates")  # type: ignore[arg-type, call-overload]
graph.add_node("Writer", writer, streams="values")  # type: ignore[arg-type, call-overload]
graph.add_node("Critic", critic, streams="values")  # type: ignore[arg-type, call-overload]

graph.add_edge(START, "Planner")
graph.add_edge("Researcher", "Planner")
graph.add_edge("Writer", "Critic")
graph.add_edge("Critic", END)


def planner_router(plan: PlanResult) -> str:
    """Route based on planner confidence.

    Returns ``"research"`` when ``plan.confidence < 0.9`` else ``"write"``.
    """

    return "research" if plan.confidence < 0.9 else "write"


graph.add_conditional_edges(
    "Planner", planner_router, {"research": "Researcher", "write": "Writer"}
)


def create_checkpoint_saver(data_dir: Path | None = None) -> SqliteCheckpointSaver:
    """Create a SQLite checkpoint saver in ``data_dir``.

    Purpose:
        Centralize setup of the SQLite checkpoint saver used for graph runs.

    Inputs:
        data_dir: Optional root directory for the database. Defaults to
            ``Settings.data_dir``.

    Outputs:
        Instance of :class:`SqliteCheckpointSaver` bound to ``checkpoint.db``.

    Side Effects:
        Creates ``data_dir`` and ``checkpoint.db`` if they do not exist.

    Exceptions:
        Propagated from filesystem operations or saver initialization.
    """

    data_dir = data_dir or Settings().data_dir  # type: ignore[call-arg]
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "checkpoint.db"

    try:
        return SqliteCheckpointSaver(path=str(db_path))  # type: ignore[arg-type]
    except TypeError:  # pragma: no cover - fallback for older API
        conn = sqlite3.connect(db_path, check_same_thread=False)
        return SqliteCheckpointSaver(conn)  # type: ignore[arg-type]


def compile_with_sqlite_checkpoint(
    graph: StateGraph, data_dir: Path | None = None
) -> CompiledStateGraph:
    """Compile ``graph`` with SQLite-backed checkpointing.

    Args:
        graph: :class:`StateGraph` to compile.
        data_dir: Optional directory for database storage.

    Returns:
        Compiled graph configured with a SQLite checkpoint saver.
    """

    saver = create_checkpoint_saver(data_dir)
    return graph.compile(checkpointer=saver)


__all__ = [
    "CitationResult",
    "PlanResult",
    "critic",
    "graph",
    "planner",
    "planner_router",
    "researcher_web",
    "writer",
    "create_checkpoint_saver",
    "compile_with_sqlite_checkpoint",
    "SqliteCheckpointSaver",
]
