"""StateGraph construction for orchestration pipeline."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, AsyncGenerator, TYPE_CHECKING

from langgraph.graph import END, START, StateGraph

if TYPE_CHECKING:  # pragma: no cover - used only for type checking
    from langgraph.graph import CompiledGraph  # type: ignore[attr-defined]
else:  # pragma: no cover - runtime import with graceful fallback
    try:
        from langgraph.graph import CompiledGraph  # type: ignore[attr-defined]
    except Exception:
        CompiledGraph = Any  # type: ignore[assignment]

from .state import ActionLog, Citation, State
from .retry import retry_async


# ``langgraph`` does not expose a stable ``CompiledGraph`` in all versions. For
# type checking, we alias it to :class:`Any` to avoid hard dependency on internal
# modules while retaining the intended semantics.
CompiledGraph = Any


def planner(state: State) -> dict:
    """Derive an initial plan from the prompt.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with planner step recorded.
    """

    state.log.append(ActionLog(message="planner"))
    return state.model_dump()


def researcher_web(state: State) -> dict:
    """Gather information from web sources with deduplication."""

    state.log.append(ActionLog(message="researcher_web"))
    seen: set[str] = set()
    deduped: list[Citation] = []
    for src in state.sources:
        lowered = src.url.lower()
        if lowered not in seen:
            seen.add(lowered)
            deduped.append(src)
    state.sources = deduped
    return state.model_dump()


def content_weaver(state: State) -> dict:
    """Weave gathered content into coherent form."""

    state.log.append(ActionLog(message="content_weaver"))
    return state.model_dump()


# TODO: Replace placeholder evaluation with real model call
async def _evaluate(state: State) -> float:  # pragma: no cover - patched in tests
    """Evaluate content and return a score.

    Args:
        state: Current orchestration state.

    Returns:
        Perfect score for placeholder implementation.
    """

    return 1.0


@retry_async(max_retries=3)
async def critic(state: State) -> dict:
    """Critically evaluate the woven content.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with critic step recorded.

    Side Effects:
        Appends ``ActionLog('critic')`` to ``state.log`` and updates
        ``critic_score`` and ``critic_attempts`` only after a successful
        evaluation.

    Exceptions:
        Propagates the last exception if all retries fail.
    """

    score = await _evaluate(state)
    state.log.append(ActionLog(message="critic"))
    state.critic_attempts += 1  # type: ignore[attr-defined]
    state.critic_score = score  # type: ignore[attr-defined]
    return asdict(state)


def approver(state: State) -> dict:
    """Approve or refine the content after critique."""

    state.log.append(ActionLog(message="approver"))
    return state.model_dump()


def exporter(state: State) -> dict:
    """Export the approved content to its final format."""

    state.log.append(ActionLog(message="exporter"))
    return state.model_dump()


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
        research_count = sum(
            1 for item in state.log if item.message == "researcher_web"
        )
        return "to_research" if research_count < 1 else "to_weaver"

    graph.add_conditional_edges(
        "planner",
        planner_router,
        {"to_research": "researcher_web", "to_weaver": "content_weaver"},
    )
    graph.add_edge("researcher_web", "planner")
    graph.add_edge("content_weaver", "critic")

    def critic_router(state: State) -> str:
        critic_count = sum(1 for item in state.log if item.message == "critic")
        return "approve" if critic_count >= 3 else "revise"

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

    async for event in app.astream(state.model_dump(), stream_mode="values"):
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

    async for event in app.astream(state.model_dump(), stream_mode="updates"):
        yield event
