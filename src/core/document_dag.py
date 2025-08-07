"""Section-wise document generation using a simple DAG."""

from __future__ import annotations

from agents.content_weaver import run_content_weaver
from agents.pedagogy_critic import run_pedagogy_critic
from agents.planner import run_planner
from agents.researcher_web_node import run_researcher_web
from core.orchestrator import END, START, Graph
from core.policies import policy_retry_on_critic_failure
from core.state import State


def _build_section_graph(section_id: int) -> Graph:
    """Construct a small graph to process a single outline section."""

    async def _draft(state: State) -> None:
        await run_content_weaver(state, section_id=section_id)

    nodes = {
        "Researcher-Web": run_researcher_web,
        "Content-Weaver": _draft,
        "Pedagogy-Critic": run_pedagogy_critic,
    }
    edges = {
        START: ["Researcher-Web"],
        "Researcher-Web": ["Content-Weaver"],
        "Content-Weaver": ["Pedagogy-Critic"],
    }
    conditionals = {
        "Pedagogy-Critic": (
            policy_retry_on_critic_failure,
            {True: "Content-Weaver", False: END},
        )
    }
    return Graph(nodes, edges, conditionals)


async def run_document_dag(state: State, skip_plan: bool = False) -> State:
    """Generate content for each outline section and merge into ``state``."""

    if not skip_plan:
        await run_planner(state)

    for idx, _ in enumerate(state.outline.steps):
        section_graph = _build_section_graph(idx)
        await section_graph.run(state)
        if state.modules:
            state.outline.steps[idx] = (
                state.modules[-1].title or state.outline.steps[idx]
            )
    state.outline.modules = list(state.modules)
    return state


__all__ = ["run_document_dag"]
