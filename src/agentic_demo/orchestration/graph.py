"""StateGraph construction for orchestration pipeline."""

from __future__ import annotations

from dataclasses import asdict
from typing import AsyncGenerator

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .state import State


# TODO: Implement real planner logic once available


def planner(state: State) -> State:
    """Derive an initial plan from the prompt.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with planner step recorded.
    """

    state.log.append("planner")
    return state


# TODO: Replace placeholder with web research implementation


def researcher_web(state: State) -> State:
    """Gather information from web sources.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with researcher step recorded.
    """

    state.log.append("researcher_web")
    return state


# TODO: Flesh out content weaving algorithm


def content_weaver(state: State) -> State:
    """Weave gathered content into coherent form.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with content weaving recorded.
    """

    state.log.append("content_weaver")
    return state


# TODO: Support multiple critic personas


def critic(state: State) -> State:
    """Critically evaluate the woven content.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with critic step recorded.
    """

    state.log.append("critic")
    return state


# TODO: Integrate human approval workflows


def approver(state: State) -> State:
    """Approve or refine the content after critique.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with approver step recorded.
    """

    state.log.append("approver")
    return state


# TODO: Export in multiple formats (PDF, DOCX, etc.)


def exporter(state: State) -> State:
    """Export the approved content to its final format.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with exporter step recorded.
    """

    state.log.append("exporter")
    return state


def create_state_graph() -> StateGraph[State]:
    """Construct the orchestration :class:`StateGraph`.

    Returns:
        Graph with all orchestration nodes wired sequentially.
    """

    graph = StateGraph(State)
    graph.add_node("planner", planner)
    graph.add_node("researcher_web", researcher_web)
    graph.add_node("content_weaver", content_weaver)
    graph.add_node("critic", critic)
    graph.add_node("approver", approver)
    graph.add_node("exporter", exporter)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "researcher_web")
    graph.add_edge("researcher_web", "content_weaver")
    graph.add_edge("content_weaver", "critic")
    graph.add_edge("critic", "approver")
    graph.add_edge("approver", "exporter")
    graph.add_edge("exporter", END)
    return graph


def compile_graph(graph: StateGraph[State] | None = None) -> CompiledStateGraph:
    """Compile a :class:`StateGraph` into a runnable graph.

    Args:
        graph: Optional pre-built graph. If ``None``, a fresh graph is created.

    Returns:
        Compiled graph ready for execution.
    """

    graph = graph or create_state_graph()
    return graph.compile()


async def stream_values(
    app: CompiledStateGraph, state: State
) -> AsyncGenerator[dict, None]:
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
    app: CompiledStateGraph, state: State
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
