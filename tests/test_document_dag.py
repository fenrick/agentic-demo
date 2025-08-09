"""Tests for sequential document generation without graph utilities."""

from __future__ import annotations

import asyncio
import sys
import types

import core.document_dag as document_dag  # noqa: E402
from core.state import Module, Outline, State

# ---------------------------------------------------------------------------
# Stub agent modules required by ``core.document_dag``.
# ---------------------------------------------------------------------------

calls: list[str] = []


async def _run_researcher_web(state: State) -> None:
    calls.append("research")


async def _run_content_weaver(state: State, section_id: int | None = None):
    calls.append("draft")
    module = Module(id=str(section_id), title=f"t{section_id}", duration_min=1)
    state.modules.append(module)
    return module


async def _run_pedagogy_critic(state: State) -> None:
    calls.append("critic")


a_research = types.ModuleType("agents.researcher_web_node")
a_research.run_researcher_web = _run_researcher_web  # type: ignore[attr-defined]
sys.modules["agents.researcher_web_node"] = a_research

a_weaver = types.ModuleType("agents.content_weaver")


class _RetryableError(RuntimeError):
    """Lightweight stand-in for the real RetryableError class."""


a_weaver.RetryableError = _RetryableError  # type: ignore[attr-defined]
a_weaver.run_content_weaver = _run_content_weaver  # type: ignore[attr-defined]
sys.modules["agents.content_weaver"] = a_weaver

a_critic = types.ModuleType("agents.pedagogy_critic")
a_critic.run_pedagogy_critic = _run_pedagogy_critic  # type: ignore[attr-defined]
sys.modules["agents.pedagogy_critic"] = a_critic

# Policy stub to satisfy imports; patched per test.
policies = types.ModuleType("core.policies")
policies.policy_retry_on_critic_failure = lambda *a, **k: False  # type: ignore[attr-defined]
sys.modules["core.policies"] = policies


def test_run_document_dag_processes_sections() -> None:
    calls.clear()
    document_dag.policy_retry_on_critic_failure = lambda *a, **k: False
    state = State(prompt="p", outline=Outline(steps=["a", "b"]))
    asyncio.run(document_dag.run_document_dag(state, skip_plan=True))
    assert calls == [
        "research",
        "draft",
        "critic",
        "research",
        "draft",
        "critic",
    ]
    assert len(state.modules) == 2
    assert state.outline.modules == state.modules


def test_run_document_dag_retries_on_critic_feedback() -> None:
    calls.clear()

    class Report:
        def __init__(self, recommendations: list[str]):
            self.recommendations = recommendations

    reports = iter([Report(["revise"]), Report([])])

    async def _critic(state: State) -> Report:  # type: ignore[override]
        calls.append("critic")
        return next(reports)

    document_dag.run_pedagogy_critic = _critic
    document_dag.policy_retry_on_critic_failure = lambda report, _state: bool(
        report.recommendations
    )

    state = State(prompt="p", outline=Outline(steps=["a"]))
    asyncio.run(document_dag.run_document_dag(state, skip_plan=True))
    assert calls == ["research", "draft", "critic", "draft", "critic"]
