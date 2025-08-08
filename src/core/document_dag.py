"""Section-wise document generation using sequential nodes."""

from __future__ import annotations

from typing import Awaitable, Callable

from agents.content_weaver import run_content_weaver
from agents.pedagogy_critic import run_pedagogy_critic
from agents.planner import run_planner
from agents.researcher_web_node import run_researcher_web
from core.policies import policy_retry_on_critic_failure
from core.state import State

NodeCallable = Callable[[State], Awaitable[object]]


def _build_section_graph(section_id: int) -> list[NodeCallable]:
    """Return the callables needed to process a single outline section."""

    async def _draft(state: State) -> None:
        await run_content_weaver(state, section_id=section_id)

    return [run_researcher_web, _draft, run_pedagogy_critic]


async def run_document_dag(state: State, skip_plan: bool = False) -> State:
    """Generate content for each outline section and merge into ``state``."""

    if not skip_plan:
        await run_planner(state)

    for idx, _ in enumerate(state.outline.steps):
        researcher, draft, critic = _build_section_graph(idx)
        await researcher(state)
        while True:
            await draft(state)
            report = await critic(state)
            if not policy_retry_on_critic_failure(report, state):
                break
        if state.modules:
            state.outline.steps[idx] = (
                state.modules[-1].title or state.outline.steps[idx]
            )
    state.outline.modules = list(state.modules)
    return state


__all__ = ["run_document_dag"]
