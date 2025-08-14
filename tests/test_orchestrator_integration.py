"""Integration tests for the orchestrator's main flow."""

from __future__ import annotations

import sys
import types
from contextlib import asynccontextmanager
from typing import Any, Callable

import pytest

from agents.content_weaver import RetryableError
from core.state import State


@pytest.mark.asyncio
async def test_full_flow_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    """GraphOrchestrator runs through the full happy path."""

    order: list[str] = []

    # Provide lightweight stubs to avoid heavy imports
    researcher_stub = types.ModuleType("agents.researcher_web_node")

    async def run_researcher_web(_state: State) -> dict[str, str]:
        order.append("Researcher-Web")
        return {"node": "Researcher-Web"}

    researcher_stub.run_researcher_web = run_researcher_web  # type: ignore[attr-defined]
    sys.modules["agents.researcher_web_node"] = researcher_stub

    exporter_stub = types.ModuleType("agents.exporter")

    async def run_exporter(_state: State) -> dict[str, str]:
        order.append("Exporter")
        return {"node": "Exporter"}

    exporter_stub.run_exporter = run_exporter  # type: ignore[attr-defined]
    sys.modules["agents.exporter"] = exporter_stub

    from core.orchestrator import GraphOrchestrator, build_main_flow

    def make_stub(name: str) -> Callable[[State], Any]:
        async def _stub(state: State) -> Any:
            order.append(name)
            return {"node": name}

        return _stub

    for func, name in [
        ("run_planner", "Planner"),
        ("run_learning_advisor", "Learning-Advisor"),
        ("run_content_weaver", "Content-Weaver"),
        ("run_content_rewriter", "Content-Rewriter"),
        ("run_final_reviewer", "Final-Reviewer"),
    ]:
        monkeypatch.setattr(f"core.orchestrator.{func}", make_stub(name))

    class _Feedback:
        needs_revision = False

    async def _editor_stub(state: State) -> Any:
        order.append("Editor")
        return _Feedback()

    monkeypatch.setattr("core.orchestrator.run_editor", _editor_stub)

    class DummySpan:
        def __enter__(self) -> "DummySpan":  # pragma: no cover - trivial
            return self

        def __exit__(self, *exc: Any) -> None:  # pragma: no cover - trivial
            return None

        def set_attributes(
            self, *_a: Any, **_k: Any
        ) -> None:  # pragma: no cover - trivial
            return None

    async def dummy_log_action(
        *_a: Any, **_k: Any
    ) -> None:  # pragma: no cover - trivial
        return None

    @asynccontextmanager
    async def dummy_session():  # pragma: no cover - trivial
        yield object()

    monkeypatch.setattr("core.orchestrator.logfire.span", lambda *_a, **_k: DummySpan())
    monkeypatch.setattr("core.orchestrator.log_action", dummy_log_action)
    monkeypatch.setattr("core.orchestrator.get_db_session", dummy_session)
    monkeypatch.setattr("core.orchestrator.compute_hash", lambda _i: "h")

    orch = GraphOrchestrator(build_main_flow())
    await orch.run(State(prompt="topic"))

    assert order == [
        "Researcher-Web",
        "Planner",
        "Learning-Advisor",
        "Content-Weaver",
        "Editor",
        "Final-Reviewer",
        "Exporter",
    ]


@pytest.mark.asyncio
async def test_validation_error_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid model output surfaces as a :class:`RetryableError`."""

    # Stub modules before importing orchestrator
    researcher_stub = types.ModuleType("agents.researcher_web_node")

    async def _run_researcher(
        _state: State,
    ) -> dict[str, str]:  # pragma: no cover - stub
        return {"node": "research"}

    researcher_stub.run_researcher_web = _run_researcher  # type: ignore[attr-defined]
    sys.modules["agents.researcher_web_node"] = researcher_stub

    exporter_stub = types.ModuleType("agents.exporter")

    async def _run_exporter(_state: State) -> dict[str, str]:  # pragma: no cover - stub
        return {"node": "export"}

    exporter_stub.run_exporter = _run_exporter  # type: ignore[attr-defined]
    sys.modules["agents.exporter"] = exporter_stub

    from core.orchestrator import GraphOrchestrator, build_main_flow

    async def planner(state: State) -> Any:
        return {"plan": True}

    monkeypatch.setattr("core.orchestrator.run_planner", planner)

    async def bad_call(_prompt: str) -> Any:
        async def gen():
            yield "{}"  # missing required fields

        return gen()

    monkeypatch.setattr("agents.content_weaver.call_openai_function", bad_call)
    monkeypatch.setattr("agents.content_weaver.stream_messages", lambda *_a, **_k: None)
    monkeypatch.setattr("agents.content_weaver.stream_debug", lambda *_a, **_k: None)

    class DummySpan:
        def __enter__(self) -> "DummySpan":  # pragma: no cover - trivial
            return self

        def __exit__(self, *exc: Any) -> None:  # pragma: no cover - trivial
            return None

        def set_attributes(
            self, *_a: Any, **_k: Any
        ) -> None:  # pragma: no cover - trivial
            return None

    async def dummy_log_action(
        *_a: Any, **_k: Any
    ) -> None:  # pragma: no cover - trivial
        return None

    @asynccontextmanager
    async def dummy_session():  # pragma: no cover - trivial
        yield object()

    monkeypatch.setattr("core.orchestrator.logfire.span", lambda *_a, **_k: DummySpan())
    monkeypatch.setattr("core.orchestrator.log_action", dummy_log_action)
    monkeypatch.setattr("core.orchestrator.get_db_session", dummy_session)
    monkeypatch.setattr("core.orchestrator.compute_hash", lambda _i: "h")

    orch = GraphOrchestrator(build_main_flow())
    with pytest.raises(RetryableError):
        await orch.run(State(prompt="topic"))
