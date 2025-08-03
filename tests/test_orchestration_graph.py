"""Tests for orchestration graph construction and streaming."""

import pytest

from agentic_demo.orchestration import (
    compile_graph,
    create_state_graph,
    researcher_web,
    stream_updates,
    stream_values,
    researcher_web,
)
from agentic_demo.orchestration.state import State
from langgraph.graph import END, START


def test_graph_nodes_and_edges() -> None:
    """Graph should include all nodes and policy-driven edges."""
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
        ("researcher_web", "planner"),
        ("content_weaver", "critic"),
        ("approver", "exporter"),
        ("exporter", END),
    }


@pytest.mark.skip(reason="Streaming loop requires full state model not yet implemented")
@pytest.mark.asyncio
async def test_streaming_with_internal_critic_retries():
    """Streaming should reflect planner-researcher loop with internal critic retries."""
    app = compile_graph()
    state = State(prompt="question", sources=["A", "a", "B"])
    values = [event async for event in stream_values(app, state)]
    updates = [event async for event in stream_updates(app, state)]
    expected_updates = [
        "planner",
        "researcher_web",
        "planner",
        "content_weaver",
        "critic",
        "content_weaver",
        "critic",
        "content_weaver",
        "critic",
        "approver",
        "exporter",
    ]
    assert [list(event.keys())[0] for event in updates] == expected_updates
    assert [entry["message"] for entry in values[-1]["log"]] == expected_updates
    assert [s["url"] for s in values[-1]["sources"]] == ["A", "B"]
    assert sum(1 for entry in values[-1]["log"] if entry["message"] == "critic") == 3
    assert sum(1 for entry in values[-1]["log"] if entry == "critic") == 3


def test_researcher_semantic_dedup():
    """Researcher should deduplicate sources case-insensitively."""
    state = State(sources=["A", "a", "B"])
    result = researcher_web(state)
    assert result["sources"] == ["A", "B"]
