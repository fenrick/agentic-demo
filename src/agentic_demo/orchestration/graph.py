"""StateGraph construction for orchestration pipeline."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, AsyncGenerator

from langgraph.graph import END, START, StateGraph

from .state import State

# ``langgraph`` does not expose a stable ``CompiledGraph`` in all versions. For
# type checking, we alias it to :class:`Any` to avoid hard dependency on internal
# modules while retaining the intended semantics.
CompiledGraph = Any


# TODO: Implement real planner logic once available


def planner(state: State) -> dict:
    """Derive an initial plan from the prompt.

    Increments planner confidence to simulate refinement.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with planner step recorded.
    """

    state.log.append("planner")
    state.confidence = min(state.confidence + 0.5, 1.0)
    return asdict(state)


# TODO: Replace placeholder with web research implementation


def researcher_web(state: State) -> dict:
    """Gather information from web sources with deduplication.

    Performs a simple case-insensitive deduplication of ``state.sources`` to
    emulate semantic merge of parallel research tasks.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with researcher step recorded.
    """

    state.log.append("researcher_web")
    seen = set()
    deduped = []
    for src in state.sources:
        lowered = src.lower()
        if lowered not in seen:
            seen.add(lowered)
            deduped.append(src)
    state.sources = deduped
    return asdict(state)


# TODO: Flesh out content weaving algorithm


def content_weaver(state: State) -> dict:
    """Weave gathered content into coherent form.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with content weaving recorded.
    """

    state.log.append("content_weaver")
    return asdict(state)


# TODO: Support multiple critic personas


def critic(state: State) -> dict:
    """Critically evaluate the woven content.

    Increments the ``critic_attempts`` counter and assigns a ``critic_score``.
    The third attempt succeeds with a score of ``1.0`` to emulate retry logic.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with critic step recorded.
    """

    state.log.append("critic")
    state.critic_attempts += 1
    state.critic_score = 1.0 if state.critic_attempts >= 3 else 0.0
    return asdict(state)


# TODO: Integrate human approval workflows


def approver(state: State) -> dict:
    """Approve or refine the content after critique.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with approver step recorded.
    """

    state.log.append("approver")
    return asdict(state)


# TODO: Export in multiple formats (PDF, DOCX, etc.)


def exporter(state: State) -> dict:
    """Export the approved content to its final format.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with exporter step recorded.
    """

    state.log.append("exporter")
    return asdict(state)


def create_state_graph() -> StateGraph:
    """Construct the orchestration :class:`StateGraph`.

    Returns:
        Graph with all orchestration nodes wired with policy-driven edges.
    """

    graph = StateGraph(State)
    graph.add_node("planner", planner)
    graph.add_node("researcher_web", researcher_web)
    graph.add_node("content_weaver", content_weaver)
    graph.add_node("critic", critic)
    graph.add_node("approver", approver)
    graph.add_node("exporter", exporter)
    graph.add_edge(START, "planner")

    def planner_router(state: State) -> str:
        return "to_weaver" if state.confidence >= 0.9 else "to_research"

    graph.add_conditional_edges(
        "planner",
        planner_router,
        {"to_research": "researcher_web", "to_weaver": "content_weaver"},
    )
    graph.add_edge("researcher_web", "planner")
    graph.add_edge("content_weaver", "critic")

    def critic_router(state: State) -> str:
        return (
            "approve"
            if state.critic_score >= 0.5 or state.critic_attempts >= 3
            else "revise"
        )

    graph.add_conditional_edges(
        "critic",
        critic_router,
        {"revise": "content_weaver", "approve": "approver"},
    )
    graph.add_edge("approver", "exporter")
    graph.add_edge("exporter", END)
    return graph


def compile_graph(graph: StateGraph | None = None) -> CompiledGraph:
    """Compile a :class:`StateGraph` into a runnable graph.

    Args:
        graph: Optional pre-built graph. If ``None``, a fresh graph is created.

    Returns:
        Compiled graph ready for execution.
    """

    graph = graph or create_state_graph()
    return graph.compile()


async def stream_values(app: CompiledGraph, state: State) -> AsyncGenerator[dict, None]:
    """Yield state values emitted by the graph.

    Args:
        app: Compiled graph application.
        state: Initial state for execution.

    Yields:
        Mapping of node name to state values for each step.
    """

    async for event in app.astream(asdict(state), stream_mode="values"):
        yield event


async def stream_updates(
    app: CompiledGraph, state: State
) -> AsyncGenerator[dict, None]:
    """Yield incremental state updates from the graph.

    Args:
        app: Compiled graph application.
        state: Initial state for execution.

    Yields:
        Mapping of node name to partial state updates per step.
    """

    async for event in app.astream(asdict(state), stream_mode="updates"):
        yield event
