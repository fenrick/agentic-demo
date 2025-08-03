"""LangGraph-based orchestration stubs.

This module wires together placeholder nodes using :class:`langgraph.graph.StateGraph`.
Each node is intentionally minimal and will be expanded with real logic in future
iterations.
"""

from __future__ import annotations

from dataclasses import dataclass
import asyncio
import sqlite3
from pathlib import Path
from typing import Dict, List

from langgraph.graph import END, START, StateGraph
from tenacity import retry, stop_after_attempt

from agentic_demo.config import Settings
from core.state import ActionLog, Outline, State
from web.researcher_web import CitationResult, researcher_web as _web_research

try:  # pragma: no cover - import path varies with package version
    from langgraph_checkpoint_sqlite import SqliteCheckpointSaver  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from langgraph.checkpoint.sqlite import SqliteSaver as SqliteCheckpointSaver

from core.state import State
from core.agents import planner, researcher_web, content_weaver, pedagogy_critic, fact_checker, approver, exporter


@dataclass(slots=True)
class PlanResult:
    """Output of the planner node.

    Attributes:
        outline: Proposed structure for downstream processing.
        confidence: Heuristic confidence score in the plan.
    """

    outline: Outline | None = None
    confidence: float = 0.0





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
graph.add_node(planner, name="Planner", streams="values")
graph.add_node(researcher_web, name="Researcher-Web", streams="updates")
graph.add_node(content_weaver, name="Content-Weaver", streams="messages")
graph.add_node(pedagogy_critic, name="Pedagogy-Critic", streams="debug")
graph.add_node(fact_checker, name="Fact-Checker", streams="debug")
graph.add_node(approver, name="Human-In-Loop", streams="values")
graph.add_node(exporter, name="Exporter")

graph.add_edge(START, "Planner")
graph.add_edge("Planner", "Researcher-Web")
graph.add_edge("Researcher-Web", "Content-Weaver")
graph.add_edge("Content-Weaver", "Pedagogy-Critic")
graph.add_edge("Content-Weaver", "Fact-Checker")
graph.add_edge("Pedagogy-Critic", "Approver")
graph.add_edge("Fact-Checker", "Approver")
graph.add_edge("Approver", "Exporter")
graph.add_edge("Exporter", END)


def planner_router(plan: PlanResult) -> str:
    """Route based on planner confidence.

    Returns ``"research"`` when ``plan.confidence < 0.9`` else ``"write"``.
    """

    return "research" if plan.confidence < 0.9 else "write"


graph.add_conditional_edges(
    "Planner", planner_router, {"research": "Researcher", "write": "Writer"}
)


# Configure checkpoint saver


def create_checkpoint_saver(data_dir: Path | None = None) -> SqliteCheckpointSaver:
    """Create a SQLite checkpoint saver in ``data_dir``."""

    data_dir = data_dir or Settings().data_dir  # type: ignore[call-arg]
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "checkpoint.db"
    try:
        return SqliteCheckpointSaver(path=str(db_path))  # type: ignore[arg-type]
    except TypeError:  # pragma: no cover - handle async variant
        try:
            from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
            import aiosqlite

            async def _create() -> AsyncSqliteSaver:
                conn = await aiosqlite.connect(db_path)
                return AsyncSqliteSaver(conn)

            return asyncio.run(_create())  # type: ignore[return-value]
        except Exception:  # pragma: no cover - fallback to sync connection
            conn = sqlite3.connect(db_path, check_same_thread=False)
            return SqliteCheckpointSaver(conn)  # type: ignore[arg-type]


saver = create_checkpoint_saver()
try:  # pragma: no cover - method added in recent versions
    graph.set_checkpoint_saver(saver)  # type: ignore[attr-defined]
except AttributeError:
    graph.checkpointer = saver  # type: ignore[attr-defined]


__all__ = [
    "CitationResult",
    "PlanResult",
    "critic",
    "graph",
    "planner",
    "planner_router",
    "researcher_web",
    "writer",
]
