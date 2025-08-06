"""LangGraph orchestration and node registration."""

from __future__ import annotations

import contextlib
import importlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional, TypeVar, cast

import tiktoken
import config
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langsmith import Client
from opentelemetry import trace

from agents.planner import PlanResult
from core.checkpoint import SqliteCheckpointManager
from core.logging import get_logger
from core.state import State
from persistence import get_db_session
from persistence.logs import compute_hash, log_action

logger = get_logger()
tracer = trace.get_tracer(__name__)

try:
    _ENCODING = tiktoken.encoding_for_model(config.MODEL_NAME)
except KeyError:
    _ENCODING = tiktoken.get_encoding("cl100k_base")


try:
    langsmith_client: Client | None = Client()
except Exception:  # pragma: no cover - optional client
    logger.exception("LangSmith client disabled")
    langsmith_client = None


def _token_count(payload: object) -> int:
    """Return tiktoken token length for ``payload``."""

    dumped = json.dumps(payload, sort_keys=True, default=str)
    return len(_ENCODING.encode(dumped))


def validate_model_configuration() -> None:
    """Ensure the configured model matches the enforced default.

    Loads :mod:`config` settings on demand to avoid requiring environment
    variables at import time.
    """

    configured = config.load_settings().model_name
    if configured != config.MODEL_NAME:
        raise ValueError(
            f"MODEL_NAME misconfigured: expected '{config.MODEL_NAME}', got"
            f" '{configured}'"
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


def _coerce_mapping_key(key: str) -> str | bool:
    """Return ``key`` converted to native bool when applicable.

    The JSON graph specification stores mapping keys as strings. When a
    condition function returns a boolean value the keys "True" and "False"
    would not match the mapping without conversion. This helper ensures that
    such keys are converted to their boolean counterparts while leaving other
    values untouched.
    """

    lower = key.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    return key


class GraphOrchestrator:
    """Construct a LangGraph graph from a JSON specification."""

    def __init__(
        self,
        checkpoint_manager: SqliteCheckpointManager | None = None,
        spec_path: Path | None = None,
        langsmith_client: Client | None = langsmith_client,
    ) -> None:
        self._graph: Optional[StateGraph[State]] = None
        self.graph: Optional[CompiledStateGraph[State]] = None
        self.checkpoint_manager = checkpoint_manager
        self.langsmith_client = langsmith_client
        self.spec_path = (
            spec_path or Path(__file__).resolve().parents[1] / "langgraph.json"
        )

    def _wrap(
        self, name: str, node: Callable[[State], Awaitable[T]]
    ) -> Callable[[State], Awaitable[T]]:
        async def wrapped(state: State) -> T:
            input_dict = state.to_dict()
            input_hash = compute_hash(input_dict)
            trace_ctx = (
                self.langsmith_client.trace(name, inputs=input_dict)
                if self.langsmith_client is not None
                else contextlib.nullcontext()
            )
            with trace_ctx as run:
                with tracer.start_as_current_span(name):
                    result = await node(state)
                    if self.checkpoint_manager is not None:
                        await self.checkpoint_manager.save_checkpoint(state)
                    output_hash = compute_hash(result)
                    tokens = _token_count(input_dict) + _token_count(result)
                    workspace_id = getattr(state, "workspace_id", "default")
                    async with get_db_session() as conn:
                        await log_action(
                            conn,
                            workspace_id,
                            name,
                            input_hash,
                            output_hash,
                            tokens,
                            0.0,
                            datetime.utcnow(),
                        )
                    if run is not None:
                        run.log_metrics({"token_count": tokens})
                        run.end(outputs=result)
                    return result

        wrapped.__name__ = name
        return wrapped

    def initialize_graph(self) -> None:
        """Instantiate the graph from the JSON specification."""
        with self.spec_path.open("r", encoding="utf-8") as f:
            spec = json.load(f)
        graph = StateGraph(State)
        self._edge_spec = spec.get("edges", [])
        for node in spec.get("nodes", []):
            fn = cast(
                Callable[[State], Awaitable[Any]], _import_callable(node["callable"])
            )
            graph.add_node(
                node["name"],
                self._wrap(node["name"], fn),
                streams=node.get("streams"),
            )
        self._graph = graph

    def register_edges(self) -> None:
        """Wire node-to-node transitions from the JSON spec."""
        if self._graph is None:
            raise RuntimeError("Graph must be initialized before registering edges")
        for edge in self._edge_spec:
            if "condition" in edge:
                func = _import_callable(edge["condition"])
                mapping = {
                    _coerce_mapping_key(k): _resolve_endpoint(v)
                    for k, v in edge["mapping"].items()
                }
                self._graph.add_conditional_edges(
                    _resolve_endpoint(edge["source"]),
                    func,
                    mapping,
                )
            else:
                self._graph.add_edge(
                    _resolve_endpoint(edge["source"]),
                    _resolve_endpoint(edge["target"]),
                )
        self.graph = self._graph.compile()

    async def start(self, initial_prompt: str) -> PlanResult:
        """Create initial state and invoke the planner."""
        if self.graph is None:
            self.initialize_graph()
            self.register_edges()
        state = State(prompt=initial_prompt)
        planner_fn = cast(
            Callable[[State], Awaitable[PlanResult]],
            _import_callable("agents.planner.run_planner"),
        )
        planner: Callable[[State], Awaitable[PlanResult]] = self._wrap(
            "Planner", planner_fn
        )
        return await planner(state)

    async def resume(self) -> PlanResult:
        """Resume a previously checkpointed run."""
        if self.graph is None:
            self.initialize_graph()
            self.register_edges()
        if self.checkpoint_manager is None:
            raise RuntimeError("Checkpoint manager required to resume")
        state = await self.checkpoint_manager.load_checkpoint()
        planner_fn = cast(
            Callable[[State], Awaitable[PlanResult]],
            _import_callable("agents.planner.run_planner"),
        )
        planner: Callable[[State], Awaitable[PlanResult]] = self._wrap(
            "Planner", planner_fn
        )
        return await planner(state)


def _create_checkpoint_manager(data_dir: Path | None = None) -> SqliteCheckpointManager:
    settings = config.load_settings()
    data_dir = data_dir or settings.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "checkpoint.db"
    return SqliteCheckpointManager(str(db_path))


checkpoint_manager = _create_checkpoint_manager()

graph_orchestrator = GraphOrchestrator(
    checkpoint_manager, langsmith_client=langsmith_client
)
graph_orchestrator.initialize_graph()
graph_orchestrator.register_edges()

graph = graph_orchestrator.graph

__all__ = [
    "GraphOrchestrator",
    "PlanResult",
    "graph",
    "checkpoint_manager",
    "langsmith_client",
]
