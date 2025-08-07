"""Lightweight orchestration over a simple node pipeline.

Each node is wrapped with :func:`wrap_with_tracing` so that execution occurs
inside a ``logfire`` span capturing input/output hashes and token counts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar

import config
import logfire
import tiktoken

from agents.planner import PlanResult  # noqa: F401
from agents.planner import run_planner
from agents.researcher_web_node import run_researcher_web
from agents.content_weaver import run_content_weaver
from agents.pedagogy_critic import run_pedagogy_critic
from agents.fact_checker import run_fact_checker
from agents.approver import run_approver
from agents.exporter import run_exporter
from core.logging import get_logger
from core.policies import (
    policy_retry_on_critic_failure,
    policy_retry_on_low_confidence,
)
from core.state import State
from persistence import get_db_session
from persistence.logs import compute_hash, log_action

logger = get_logger()

try:
    _ENCODING = tiktoken.encoding_for_model(config.DEFAULT_MODEL_NAME)
except KeyError:  # pragma: no cover - fallback for unknown models
    _ENCODING = tiktoken.get_encoding("cl100k_base")


def _token_count(payload: object) -> int:
    """Return tiktoken token length for ``payload``."""

    dumped = json.dumps(payload, sort_keys=True, default=str)
    return len(_ENCODING.encode(dumped))


def validate_model_configuration() -> None:
    """Ensure the configured model matches the enforced default."""

    configured = config.load_settings().model
    if configured != config.MODEL:
        raise ValueError(
            f"MODEL misconfigured: expected '{config.MODEL}', got '{configured}'"
        )
    logger.info("Using LLM engine %s", config.MODEL)


validate_model_configuration()

T = TypeVar("T")


def wrap_with_tracing(
    fn: Callable[[State], Awaitable[T]],
) -> Callable[[State], Awaitable[T]]:
    """Wrap ``fn`` to trace inputs, outputs and token usage.

    A ``logfire`` span is opened using the function name. The span records
    hashes of the input and output payloads along with the total token count.
    """

    async def wrapped(state: State) -> T:
        name = fn.__name__
        input_dict = state.to_dict()
        input_hash = compute_hash(input_dict)
        with logfire.span(name, inputs=input_dict, input_hash=input_hash) as span:
            result = await fn(state)
            output_hash = compute_hash(result)
            tokens = _token_count(input_dict) + _token_count(result)
            span.set_attributes({"output_hash": output_hash, "token_count": tokens})
            if isinstance(result, dict):
                span.set_attributes({"outputs": result})
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
            logfire.trace("completed node {node}", node=name, token_count=tokens)
            return result

    wrapped.__name__ = fn.__name__
    return wrapped


@dataclass
class Node:
    """Single executable unit within the processing pipeline."""

    name: str
    fn: Callable[[State], Awaitable[Any]]
    next: Optional[str]
    condition: Optional[Callable[[Any, State], Optional[str]]] = None


def build_main_flow() -> List[Node]:
    """Return the ordered list of nodes forming the primary pipeline."""

    def planner_condition(result: PlanResult, state: State) -> Optional[str]:
        decision = policy_retry_on_low_confidence(result, state)
        return "Researcher-Web" if decision == "loop" else "Content-Weaver"

    def pedagogy_condition(report: Any, state: State) -> Optional[str]:
        return (
            "Content-Weaver"
            if policy_retry_on_critic_failure(report, state)
            else "Fact-Checker"
        )

    def factcheck_condition(report: Any, state: State) -> Optional[str]:
        return (
            "Content-Weaver"
            if policy_retry_on_critic_failure(report, state)
            else "Human-In-Loop"
        )

    return [
        Node(
            "Planner",
            wrap_with_tracing(run_planner),
            "Content-Weaver",
            planner_condition,
        ),
        Node("Researcher-Web", wrap_with_tracing(run_researcher_web), "Planner"),
        Node(
            "Content-Weaver",
            wrap_with_tracing(run_content_weaver),
            "Pedagogy-Critic",
        ),
        Node(
            "Pedagogy-Critic",
            wrap_with_tracing(run_pedagogy_critic),
            "Fact-Checker",
            pedagogy_condition,
        ),
        Node(
            "Fact-Checker",
            wrap_with_tracing(run_fact_checker),
            "Human-In-Loop",
            factcheck_condition,
        ),
        Node("Human-In-Loop", wrap_with_tracing(run_approver), "Exporter"),
        Node("Exporter", wrap_with_tracing(run_exporter), None),
    ]


class GraphOrchestrator:
    """Execute nodes sequentially according to the defined pipeline."""

    def __init__(self, flow: List[Node]):
        self.flow = flow
        self._lookup: Dict[str, Node] = {n.name: n for n in self.flow}

    async def run(self, state: State) -> State:
        """Run the pipeline for ``state``."""

        current = self.flow[0]
        while current:
            try:
                result = await current.fn(state)
            except Exception:
                logger.exception("Node %s failed", current.name)
                raise
            next_name = current.next
            if current.condition is not None:
                try:
                    next_name = current.condition(result, state)
                except Exception:
                    logger.exception("Condition for %s failed", current.name)
                    raise
            if next_name is None:
                break
            current = self._lookup[next_name]
        return state

    async def stream(self, state: State):
        """Yield progress events for each executed node."""

        current = self.flow[0]
        while current:
            yield {"type": "action", "payload": current.name}
            try:
                result = await current.fn(state)
            except Exception:
                logger.exception("Node %s failed", current.name)
                raise
            yield {"type": "state", "payload": state.to_dict()}
            next_name = current.next
            if current.condition is not None:
                try:
                    next_name = current.condition(result, state)
                except Exception:
                    logger.exception("Condition for %s failed", current.name)
                    raise
            if next_name is None:
                break
            current = self._lookup[next_name]


graph_orchestrator = GraphOrchestrator(build_main_flow())

graph = graph_orchestrator

__all__ = [
    "Node",
    "GraphOrchestrator",
    "PlanResult",
    "build_main_flow",
    "graph_orchestrator",
    "graph",
]
