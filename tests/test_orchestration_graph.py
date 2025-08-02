"""Tests for orchestration graph construction and streaming."""

import pytest

from agentic_demo.orchestration import (
    compile_graph,
    create_state_graph,
    stream_updates,
    stream_values,
)
from agentic_demo.orchestration.state import State
from langgraph.graph import END, START


def test_graph_nodes_and_edges():
    """Graph should include all nodes and sequential edges."""
    graph = create_state_graph()
    assert set(graph.nodes) == {
        "planner",
        "researcher_web",
        "content_weaver",
        "critic",
        "approver",
        "exporter",
    }
    assert graph.edges == {
        (START, "planner"),
        ("planner", "researcher_web"),
        ("researcher_web", "content_weaver"),
        ("content_weaver", "critic"),
        ("critic", "approver"),
        ("approver", "exporter"),
        ("exporter", END),
    }


@pytest.mark.asyncio
async def test_stream_values_and_updates():
    """Streaming should emit events for each orchestration step."""
    app = compile_graph()
    state = State(prompt="question")
    values = [event async for event in stream_values(app, state)]
    updates = [event async for event in stream_updates(app, state)]
    expected = [
        "planner",
        "researcher_web",
        "content_weaver",
        "critic",
        "approver",
        "exporter",
    ]
    assert len(values) == len(expected) + 1  # includes initial state
    assert [list(event.keys())[0] for event in updates] == expected
    assert values[-1]["log"] == expected
