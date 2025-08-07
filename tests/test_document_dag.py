"""Verify document DAG orchestration using the internal graph executor."""

from __future__ import annotations

import asyncio
import sys
import types

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
a_weaver.run_content_weaver = _run_content_weaver  # type: ignore[attr-defined]
sys.modules["agents.content_weaver"] = a_weaver

a_critic = types.ModuleType("agents.pedagogy_critic")
a_critic.run_pedagogy_critic = _run_pedagogy_critic  # type: ignore[attr-defined]
sys.modules["agents.pedagogy_critic"] = a_critic

# Policy stub to bypass retry logic.
policies = types.ModuleType("core.policies")
policies.policy_retry_on_critic_failure = lambda *a, **k: False  # type: ignore[attr-defined]
sys.modules["core.policies"] = policies

from core.document_dag import run_document_dag  # noqa: E402


def test_run_document_dag_processes_sections() -> None:
    state = State(prompt="p", outline=Outline(steps=["a", "b"]))
    asyncio.run(run_document_dag(state, skip_plan=True))
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
