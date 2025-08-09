"""Unit tests for the simple orchestrator pipeline."""

from __future__ import annotations

import asyncio
import sys
import types

from core.orchestrator import GraphOrchestrator, Node  # noqa: E402
from core.state import ActionLog, State  # noqa: E402

# Stubs required before importing orchestrator

# Minimal logfire replacement
logfire_stub = types.ModuleType("logfire")


class _Span:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def set_attributes(self, *a, **k):
        pass


logfire_stub.span = lambda *a, **k: _Span()  # type: ignore[attr-defined]
logfire_stub.trace = lambda *a, **k: None  # type: ignore[attr-defined]
sys.modules["logfire"] = logfire_stub  # type: ignore[assignment]

# Lightweight policy stubs
policies_stub = types.ModuleType("core.policies")
policies_stub.policy_retry_on_low_confidence = (  # type: ignore[attr-defined]
    lambda *_a, **_k: "continue"
)
policies_stub.policy_retry_on_critic_failure = (  # type: ignore[attr-defined]
    lambda *_a, **_k: False
)
sys.modules["core.policies"] = policies_stub  # type: ignore[assignment]


# Agent stubs used by build_main_flow
async def _noop(state):  # pragma: no cover - simple placeholder
    return None


for name in [
    "agents.researcher_web_node",
    "agents.content_weaver",
    "agents.pedagogy_critic",
    "agents.fact_checker",
    "agents.approver",
    "agents.exporter",
]:
    mod = types.ModuleType(name)
    mod.__dict__["run_" + name.split(".")[-1]] = _noop
    if name == "agents.content_weaver":

        class _RetryableError(RuntimeError):
            """Stubbed RetryableError to satisfy downstream imports."""

        mod.RetryableError = _RetryableError
    sys.modules[name] = mod


async def _first(state: State) -> str:
    state.log.append(ActionLog(message="first"))
    return "go"


async def _second(state: State) -> None:
    state.log.append(ActionLog(message="second"))


async def _third(state: State) -> None:
    state.log.append(ActionLog(message="third"))


def _cond(result: str, state: State) -> str | None:  # pragma: no cover - simple
    return "second" if result == "go" else None


async def run_flow() -> list[str]:
    flow = [
        Node("A", _first, "third", _cond),
        Node("second", _second, "third"),
        Node("third", _third, None),
    ]
    orch = GraphOrchestrator(flow)
    state = State(prompt="topic")
    await orch.run(state)
    return [entry.message for entry in state.log]


def test_orchestrator_condition_branching() -> None:
    """Nodes are executed based on conditional next mapping."""

    messages = asyncio.run(run_flow())
    assert messages == ["first", "second", "third"]
