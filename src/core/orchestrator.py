"""Lightweight orchestration over a JSON-defined DAG."""

from __future__ import annotations

import contextlib
import importlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional, TypeVar, cast

import tiktoken
import config
from langsmith import Client
from langsmith.run_helpers import trace as ls_trace
from opentelemetry import trace

from agents.planner import PlanResult  # noqa: F401
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


START = "START"
END = "END"


class Graph:
    """Simple directed acyclic graph executor."""

    def __init__(
        self,
        nodes: dict[str, Callable[[State], Awaitable[Any]]],
        edges: dict[str, list[str]],
        conditionals: dict[str, tuple[Callable[[State], Any], dict[Any, str]]],
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        self.conditionals = conditionals

    async def invoke(self, name: str, state: State, **kwargs: Any) -> Any:
        """Execute a single node by ``name``."""

        fn = self.nodes[name]
        return await fn(state, **kwargs)

    async def run(self, state: State) -> State:
        """Run nodes sequentially starting from ``START`` until ``END``."""

        current = START
        while True:
            next_nodes = self.edges.get(current, [])
            if not next_nodes:
                break
            node = next_nodes[0]
            if node == END:
                break
            await self.nodes[node](state)
            if node in self.conditionals:
                cond, mapping = self.conditionals[node]
                key = cond(state)
                current = mapping.get(key, END)
            else:
                current = node
        return state

    async def stream(self, state: State):
        """Yield events for each node execution."""

        current = START
        while True:
            next_nodes = self.edges.get(current, [])
            if not next_nodes:
                break
            node = next_nodes[0]
            if node == END:
                break
            yield {"type": "action", "payload": node}
            await self.nodes[node](state)
            yield {"type": "state", "payload": state.to_dict()}
            if node in self.conditionals:
                cond, mapping = self.conditionals[node]
                key = cond(state)
                current = mapping.get(key, END)
            else:
                current = node


class GraphOrchestrator:
    """Construct and execute a :class:`Graph` from a JSON specification."""

    def __init__(
        self,
        spec_path: Path | None = None,
        langsmith_client: Client | None = langsmith_client,
    ) -> None:
        self.graph: Optional[Graph] = None
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
                ls_trace(name, inputs=input_dict, client=self.langsmith_client)
                if self.langsmith_client is not None
                else contextlib.nullcontext()
            )
            async with trace_ctx as run:
                with tracer.start_as_current_span(name):
                    result = await node(state)
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
                        run.add_metadata({"token_count": tokens})
                        if isinstance(result, dict):
                            run.end(outputs=result)
                        else:
                            run.end()
                    return result

        wrapped.__name__ = name
        return wrapped

    def initialize_graph(self) -> None:
        """Instantiate the graph from the JSON specification."""

        with self.spec_path.open("r", encoding="utf-8") as f:
            spec = json.load(f)
        self._edge_spec = spec.get("edges", [])
        nodes: dict[str, Callable[[State], Awaitable[Any]]] = {}
        for node in spec.get("nodes", []):
            fn = cast(
                Callable[[State], Awaitable[Any]], _import_callable(node["callable"])
            )
            nodes[node["name"]] = self._wrap(node["name"], fn)
        self._nodes = nodes

    def register_edges(self) -> None:
        """Wire node-to-node transitions from the JSON spec."""

        edges: dict[str, list[str]] = {}
        conditionals: dict[str, tuple[Callable[[State], Any], dict[Any, str]]] = {}
        for edge in self._edge_spec:
            source = edge["source"].replace("__start__", START)
            if "condition" in edge:
                func = cast(Callable[[State], Any], _import_callable(edge["condition"]))
                mapping = {
                    _coerce_mapping_key(k): v.replace("__end__", END)
                    for k, v in edge["mapping"].items()
                }
                conditionals[source] = (func, mapping)
            else:
                target = edge["target"].replace("__end__", END)
                edges.setdefault(source, []).append(target)
        self.graph = Graph(self._nodes, edges, conditionals)


graph_orchestrator = GraphOrchestrator(langsmith_client=langsmith_client)
try:  # pragma: no cover - defensive import-time initialization
    graph_orchestrator.initialize_graph()
    graph_orchestrator.register_edges()
except Exception:  # pragma: no cover - tolerate missing spec or dependencies
    graph_orchestrator.graph = Graph({}, {}, {})

graph = graph_orchestrator.graph

__all__ = ["Graph", "GraphOrchestrator", "PlanResult", "graph", "langsmith_client"]
