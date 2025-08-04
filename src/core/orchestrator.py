"""LangGraph orchestration and node registration."""

from __future__ import annotations

import importlib
import json
import logging
from pathlib import Path
from typing import Awaitable, Callable, Optional, TypeVar

from agentic_demo import config
from agentic_demo.config import Settings
from langgraph.graph import END, START, StateGraph

from agents.planner import PlanResult
from core.checkpoint import SqliteCheckpointManager
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


def _import_callable(path: str) -> Callable[..., Awaitable | object]:
    """Import a callable from ``module:qualname`` style paths."""

    module, name = path.rsplit(".", 1)
    mod = importlib.import_module(module)
    return getattr(mod, name)


def _resolve_endpoint(name: str) -> str:
    """Translate JSON endpoint tokens to LangGraph constants."""

    if name == "__start__":
        return START
    if name == "__end__":
        return END
    return name


class GraphOrchestrator:
    """Construct a LangGraph graph from a JSON specification."""

    def __init__(
        self,
        checkpoint_manager: SqliteCheckpointManager | None = None,
        spec_path: Path | None = None,
    ) -> None:
        self.graph: Optional[StateGraph[State]] = None
        self.checkpoint_manager = checkpoint_manager
        self.spec_path = (
            spec_path or Path(__file__).resolve().parents[1] / "langgraph.json"
        )

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
        """Instantiate the graph from the JSON specification."""
        with self.spec_path.open("r", encoding="utf-8") as f:
            spec = json.load(f)
        graph = StateGraph(State)
        self._edge_spec = spec.get("edges", [])
        for node in spec.get("nodes", []):
            fn = _import_callable(node["callable"])
            graph.add_node(
                self._wrap(fn), name=node["name"], streams=node.get("streams")
            )
        self.graph = graph

    def register_edges(self) -> None:
        """Wire node-to-node transitions from the JSON spec."""
        if self.graph is None:
            raise RuntimeError("Graph must be initialized before registering edges")
        for edge in self._edge_spec:
            if "condition" in edge:
                func = _import_callable(edge["condition"])
                self.graph.add_conditional_edges(
                    _resolve_endpoint(edge["source"]),
                    func,
                    {k: _resolve_endpoint(v) for k, v in edge["mapping"].items()},
                )
            else:
                self.graph.add_edge(
                    _resolve_endpoint(edge["source"]),
                    _resolve_endpoint(edge["target"]),
                )

    async def start(self, initial_prompt: str) -> PlanResult:
        """Create initial state and invoke the planner."""
        if self.graph is None:
            self.initialize_graph()
            self.register_edges()
        state = State(prompt=initial_prompt)
        planner = self._wrap(_import_callable("agents.planner.run_planner"))
        return await planner(state)

    async def resume(self) -> PlanResult:
        """Resume a previously checkpointed run."""
        if self.graph is None:
            self.initialize_graph()
            self.register_edges()
        if self.checkpoint_manager is None:
            raise RuntimeError("Checkpoint manager required to resume")
        state = self.checkpoint_manager.load_checkpoint()
        planner = self._wrap(_import_callable("agents.planner.run_planner"))
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
