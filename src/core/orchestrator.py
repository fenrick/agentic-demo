"""LangGraph orchestration and node registration."""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from typing import Optional

from langgraph.graph import END, START, StateGraph

from agentic_demo.config import Settings
from core.state import State
from core.nodes.planner import PlanResult, run_planner
from core.nodes.researcher_web import run_researcher_web
from core.nodes.content_weaver import run_content_weaver
from core.nodes.critics import run_fact_checker, run_pedagogy_critic
from core.nodes.approver import run_approver
from core.nodes.exporter import run_exporter

try:  # pragma: no cover - import path varies with package version
    from langgraph_checkpoint_sqlite import SqliteCheckpointSaver  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from langgraph.checkpoint.sqlite import SqliteSaver as SqliteCheckpointSaver


class GraphOrchestrator:
    """Wrapper around :class:`~langgraph.graph.StateGraph` setup."""

    def __init__(self) -> None:
        self.graph: Optional[StateGraph[State]] = None

    def initialize_graph(self) -> None:
        """Instantiate the graph and register nodes."""
        graph = StateGraph(State)
        graph.add_node(run_planner, name="Planner", streams="values")
        graph.add_node(run_researcher_web, name="Researcher-Web", streams="updates")
        graph.add_node(run_content_weaver, name="Content-Weaver", streams="messages")
        graph.add_node(run_pedagogy_critic, name="Pedagogy-Critic", streams="debug")
        graph.add_node(run_fact_checker, name="Fact-Checker", streams="debug")
        graph.add_node(run_approver, name="Human-In-Loop", streams="values")
        graph.add_node(run_exporter, name="Exporter")
        self.graph = graph

    def register_edges(self) -> None:
        """Wire node-to-node transitions."""
        if self.graph is None:
            raise RuntimeError("Graph must be initialized before registering edges")
        graph = self.graph
        graph.add_edge(START, "Planner")
        graph.add_edge("Planner", "Researcher-Web")
        graph.add_edge("Researcher-Web", "Content-Weaver")
        graph.add_edge("Content-Weaver", "Pedagogy-Critic")
        graph.add_edge("Content-Weaver", "Fact-Checker")
        graph.add_edge("Pedagogy-Critic", "Human-In-Loop")
        graph.add_edge("Fact-Checker", "Human-In-Loop")
        graph.add_edge("Human-In-Loop", "Exporter")
        graph.add_edge("Exporter", END)

    async def start(self, initial_prompt: str) -> PlanResult:
        """Create initial state and invoke the planner."""
        if self.graph is None:
            self.initialize_graph()
            self.register_edges()
        state = State(prompt=initial_prompt)
        return await run_planner(state)

    async def resume(self) -> None:
        """Resume a previously checkpointed run.

        TODO: Implement checkpoint loading and continuation logic.
        """
        if self.graph is None:
            self.initialize_graph()
            self.register_edges()
        return None


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


graph_orchestrator = GraphOrchestrator()
graph_orchestrator.initialize_graph()
graph_orchestrator.register_edges()

graph = graph_orchestrator.graph
saver = create_checkpoint_saver()
try:  # pragma: no cover - method added in recent versions
    graph.set_checkpoint_saver(saver)  # type: ignore[attr-defined]
except AttributeError:
    graph.checkpointer = saver  # type: ignore[attr-defined]

__all__ = ["GraphOrchestrator", "PlanResult", "graph", "saver"]
