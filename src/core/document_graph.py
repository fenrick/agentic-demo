"""Section-wise document generation using a simple graph iterator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, List

from agents.content_weaver import run_content_weaver
from agents.pedagogy_critic import run_pedagogy_critic
from agents.planner import run_planner
from agents.researcher_web_node import run_researcher_web
from core.policies import policy_retry_on_critic_failure
from core.state import State

NodeCallable = Callable[[State], Awaitable[object]]


@dataclass
class DocumentGraph:
    """Lightweight graph executor for document generation."""

    nodes: List[NodeCallable]

    async def run(self, state: State) -> None:
        """Execute each node in order, mutating ``state`` in-place."""

        for node in self.nodes:
            await node(state)


def _build_section_graph(section_id: int) -> DocumentGraph:
    """Return the graph to process a single outline section."""

    async def draft_and_review(state: State) -> None:
        while True:
            await run_content_weaver(state, section_id=section_id)
            report = await run_pedagogy_critic(state)
            if not policy_retry_on_critic_failure(report, state):
                break
        if state.modules:
            state.outline.steps[section_id] = (
                state.modules[-1].title or state.outline.steps[section_id]
            )

    return DocumentGraph([run_researcher_web, draft_and_review])


async def run_document_graph(state: State, skip_plan: bool = False) -> State:
    """Generate content for each outline section and merge into ``state``."""

    if not skip_plan:
        await run_planner(state)

    for idx, _ in enumerate(state.outline.steps):
        section_graph = _build_section_graph(idx)
        await section_graph.run(state)
    state.outline.modules = list(state.modules)
    return state


__all__ = ["DocumentGraph", "run_document_graph"]
