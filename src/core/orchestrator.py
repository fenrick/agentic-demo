"""LangGraph orchestration and node registration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Awaitable, Callable, Optional, TypeVar

from agentic_demo import config
from agentic_demo.config import Settings
from langgraph.graph import END, START, StateGraph

from agents.approver import run_approver
from agents.content_weaver import run_content_weaver
from agents.critics import run_fact_checker, run_pedagogy_critic
from agents.exporter import run_exporter
from agents.planner import PlanResult, run_planner
from agents.researcher_web_node import run_researcher_web
from core.checkpoint import SqliteCheckpointManager
from core.policies import (policy_retry_on_critic_failure,
                           policy_retry_on_low_confidence)
from core.state import State

logger = logging.getLogger(__name__)


def validate_model_configuration() -> None:
    """Ensure the configured model matches the enforced default."""
    configured = config.settings.model_name
    if configured != config.MODEL_NAME:
        raise ValueError(
            f"MODEL_NAME misconfigured: expected '{config.MODEL_NAME}', got '{configured}'"
        )
    logger.info("Using LLM engine %s", config.MODEL_NAME)


validate_model_configuration()


T = TypeVar("T")


class GraphOrchestrator:
    """Wrapper around :class:`~langgraph.graph.StateGraph` setup."""

    def __init__(
        self, checkpoint_manager: SqliteCheckpointManager | None = None
    ) -> None:
        self.graph: Optional[StateGraph[State]] = None
        self.checkpoint_manager = checkpoint_manager

    def _wrap(
        self, node: Callable[[State], Awaitable[T]]
    ) -> Callable[[State], Awaitable[T]]:
        async def wrapped(state: State) -> T:
            result = await node(state)
            if self.checkpoint_manager is not None:
                self.checkpoint_manager.save_checkpoint(state)
            return result

        return wrapped

    def initialize_graph(self) -> None:
        """Instantiate the graph and register nodes."""
        graph = StateGraph(State)
        graph.add_node(self._wrap(run_planner), name="Planner", streams="values")
        graph.add_node(
            self._wrap(run_researcher_web), name="Researcher-Web", streams="updates"
        )
        graph.add_node(
            self._wrap(run_content_weaver), name="Content-Weaver", streams="messages"
        )
        graph.add_node(
            self._wrap(run_pedagogy_critic), name="Pedagogy-Critic", streams="debug"
        )
        graph.add_node(
            self._wrap(run_fact_checker), name="Fact-Checker", streams="debug"
        )
        graph.add_node(self._wrap(run_approver), name="Human-In-Loop", streams="values")
        graph.add_node(self._wrap(run_exporter), name="Exporter")
        self.graph = graph

    def register_edges(self) -> None:
        """Wire node-to-node transitions."""
        if self.graph is None:
            raise RuntimeError("Graph must be initialized before registering edges")
        graph = self.graph
        graph.add_edge(START, "Planner")
        graph.add_conditional_edges(
            "Planner",
            policy_retry_on_low_confidence,
            {True: "Researcher-Web", False: "Content-Weaver"},
        )
        graph.add_edge("Researcher-Web", "Planner")
        graph.add_edge("Content-Weaver", "Pedagogy-Critic")
        graph.add_edge("Content-Weaver", "Fact-Checker")
        graph.add_conditional_edges(
            "Pedagogy-Critic",
            policy_retry_on_critic_failure,
            {True: "Content-Weaver", False: "Human-In-Loop"},
        )
        graph.add_conditional_edges(
            "Fact-Checker",
            policy_retry_on_critic_failure,
            {True: "Content-Weaver", False: "Human-In-Loop"},
        )
        graph.add_edge("Human-In-Loop", "Exporter")
        graph.add_edge("Exporter", END)

    async def start(self, initial_prompt: str) -> PlanResult:
        """Create initial state and invoke the planner."""
        if self.graph is None:
            self.initialize_graph()
            self.register_edges()
        state = State(prompt=initial_prompt)
        planner = self._wrap(run_planner)
        return await planner(state)

    async def resume(self) -> PlanResult:
        """Resume a previously checkpointed run."""
        if self.graph is None:
            self.initialize_graph()
            self.register_edges()
        if self.checkpoint_manager is None:
            raise RuntimeError("Checkpoint manager required to resume")
        state = self.checkpoint_manager.load_checkpoint()
        planner = self._wrap(run_planner)
        return await planner(state)


def _create_checkpoint_manager(data_dir: Path | None = None) -> SqliteCheckpointManager:
    data_dir = data_dir or Settings().data_dir  # type: ignore[call-arg]
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "checkpoint.db"
    return SqliteCheckpointManager(str(db_path))


checkpoint_manager = _create_checkpoint_manager()

graph_orchestrator = GraphOrchestrator(checkpoint_manager)
graph_orchestrator.initialize_graph()
graph_orchestrator.register_edges()

graph = graph_orchestrator.graph

__all__ = ["GraphOrchestrator", "PlanResult", "graph", "checkpoint_manager"]
