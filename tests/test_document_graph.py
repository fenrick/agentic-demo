"""Tests for document graph iterating over outline sections."""

from __future__ import annotations

import asyncio
import sys
import types
from dataclasses import dataclass, field
from typing import List

import core.document_graph as document_graph  # noqa: E402


@dataclass
class Module:
    id: str
    title: str
    duration_min: int


@dataclass
class Outline:
    steps: List[str]
    modules: List[Module] = field(default_factory=list)


@dataclass
class State:
    prompt: str
    outline: Outline
    modules: List[Module] = field(default_factory=list)


# Provide a lightweight ``core.state`` for the module under test.
state_mod = types.ModuleType("core.state")
state_mod.Module = Module  # type: ignore[attr-defined]
state_mod.Outline = Outline  # type: ignore[attr-defined]
state_mod.State = State  # type: ignore[attr-defined]
sys.modules["core.state"] = state_mod

# ---------------------------------------------------------------------------
# Stub agent modules required by ``core.document_graph``.
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


def test_run_document_graph_processes_sections() -> None:
    calls.clear()
    document_graph.policy_retry_on_critic_failure = lambda *a, **k: False
    state = State(prompt="p", outline=Outline(steps=["a", "b"]))
    asyncio.run(document_graph.run_document_graph(state, skip_plan=True))
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


def test_run_document_graph_retries_on_critic_feedback() -> None:
    calls.clear()

    class Report:
        def __init__(self, recommendations: list[str]):
            self.recommendations = recommendations

    reports = iter([Report(["revise"]), Report([])])

    async def _critic(state: State) -> Report:  # type: ignore[override]
        calls.append("critic")
        return next(reports)

    document_graph.run_pedagogy_critic = _critic
    document_graph.policy_retry_on_critic_failure = lambda report, _state: bool(
        report.recommendations
    )

    state = State(prompt="p", outline=Outline(steps=["a"]))
    asyncio.run(document_graph.run_document_graph(state, skip_plan=True))
    assert calls == ["research", "draft", "critic", "draft", "critic"]
