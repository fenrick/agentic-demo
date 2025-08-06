"""Section-wise document generation using nested StateGraphs."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agents.content_weaver import run_content_weaver
from agents.pedagogy_critic import run_pedagogy_critic
from agents.planner import run_planner
from agents.researcher_web_node import run_researcher_web
from core.policies import policy_retry_on_critic_failure
from core.state import State


def _build_section_graph(section_id: int) -> CompiledStateGraph[State]:
    """Construct a graph to process a single outline section.

    The graph executes the Research → Draft → Critic loop for the specified
    ``section_id``. Critic failures trigger retries of the drafting step via
    :func:`policy_retry_on_critic_failure`.

    Args:
        section_id: Index of the outline section to process.

    Returns:
        CompiledStateGraph[State]: Ready-to-run graph for the section.
    """

    graph = StateGraph(State)
    graph.add_node("Researcher-Web", run_researcher_web)

    async def _draft(state: State) -> None:
        await run_content_weaver(state, section_id=section_id)

    graph.add_node("Content-Weaver", _draft)
    graph.add_node("Pedagogy-Critic", run_pedagogy_critic)
    graph.add_edge(START, "Researcher-Web")
    graph.add_edge("Researcher-Web", "Content-Weaver")
    graph.add_edge("Content-Weaver", "Pedagogy-Critic")
    graph.add_conditional_edges(
        "Pedagogy-Critic",
        policy_retry_on_critic_failure,
        {True: "Content-Weaver", False: END},
    )
    return graph.compile()


async def run_document_dag(state: State, skip_plan: bool = False) -> State:
    """Generate content for each outline section and merge into ``state``.

    Args:
        state: Current application state used across nodes.
        skip_plan: When ``True``, assumes planning has already populated
            ``state.outline`` and therefore skips the planner.

    Returns:
        State: Updated state with ``outline.modules`` reflecting generated
        sections.
    """

    if not skip_plan:
        await run_planner(state)

    for idx, _ in enumerate(state.outline.steps):
        section_graph = _build_section_graph(idx)
        invoke = getattr(section_graph, "ainvoke", None)
        if invoke is None:
            invoke = getattr(section_graph, "invoke")
        await invoke(state)  # type: ignore[func-returns-value]
        if state.modules:
            state.outline.steps[idx] = (
                state.modules[-1].title or state.outline.steps[idx]
            )
    state.outline.modules = list(state.modules)
    return state


__all__ = ["run_document_dag"]
