from unittest.mock import patch

import asyncio
import pytest

from app.primary_agent import PrimaryAgent

from app import graph
from app.graph import build_graph


def test_graph_cycles_until_review_passes():
    """Flow should repeat draft-review until review approves."""
    with (
        patch.object(graph, "plan", return_value="plan") as plan_mock,
        patch.object(graph, "research", return_value="research") as research_mock,
        patch.object(graph, "draft", return_value="draft") as draft_mock,
        patch.object(graph, "review", side_effect=["retry", "final"]) as review_mock,
    ):
        flow = build_graph()
        result = flow.run("topic")
        assert result["output"] == "final"
        assert plan_mock.called and research_mock.called
        assert draft_mock.call_count == 2
        assert review_mock.call_count == 2


def test_graph_with_overlay():
    """Overlay node should merge draft with review output when provided."""
    with (
        patch("app.graph.OverlayAgent") as Agent,
        patch.object(graph, "plan", return_value="plan"),
        patch.object(graph, "research", return_value="research"),
        patch.object(graph, "draft", return_value="draft"),
        patch.object(graph, "review", return_value="review"),
    ):
        Agent.return_value.return_value = "ov"
        flow = build_graph(mode="overlay")
        result = flow.run("topic")
        assert result["output"] == "ov"
        Agent.assert_called_once()
        Agent.return_value.assert_called_once_with("draft", "review")


def test_build_graph_mode_overlay_creates_agent():
    """mode="overlay" should instantiate OverlayAgent when not provided."""
    with (
        patch("app.graph.OverlayAgent") as Agent,
        patch.object(graph, "plan", return_value="plan"),
        patch.object(graph, "research", return_value="research"),
        patch.object(graph, "draft", return_value="draft"),
        patch.object(graph, "review", return_value="review"),
    ):
        Agent.return_value.return_value = "ov"
        flow = build_graph(mode="overlay")
        result = flow.run("topic")
        assert result["output"] == "ov"
        Agent.assert_called_once()
        Agent.return_value.assert_called_once_with("draft", "review")


@pytest.mark.asyncio
async def test_graph_async_overlay_dict():
    """Graph run should return a dict with slides or ai_overlay when overlay outputs one."""
    with (
        patch("app.graph.OverlayAgent") as Agent,
        patch.object(graph, "plan", return_value="plan"),
        patch.object(graph, "research", return_value="research"),
        patch.object(graph, "draft", return_value="draft"),
        patch.object(graph, "review", return_value="review"),
    ):
        Agent.return_value.return_value = {"slides": []}
        flow = build_graph(mode="overlay")
        result = await asyncio.to_thread(flow.run, "topic")
        assert isinstance(result["output"], dict)
        assert "slides" in result["output"] or "ai_overlay" in result["output"]
        Agent.assert_called_once()
        Agent.return_value.assert_called_once_with("draft", "review")


def test_build_graph_skip_plan():
    """skip_plan should omit plan node and start at research."""
    with (
        patch.object(graph, "plan", return_value="plan") as plan_mock,
        patch.object(graph, "research", return_value="research") as research_mock,
        patch.object(graph, "draft", return_value="draft") as draft_mock,
        patch.object(graph, "review", return_value="final") as review_mock,
    ):
        flow = build_graph(skip_plan=True)
        result = flow.run("topic")
        assert result["output"] == "final"
        plan_mock.assert_not_called()
        research_mock.assert_called_once()
        draft_mock.assert_called_once()
        review_mock.assert_called_once()


def test_overlay_history_serialized_when_dict():
    """Overlay node should append JSON when result is a dict."""
    import json

    with (
        patch("app.graph.OverlayAgent") as Agent,
        patch.object(graph, "plan", return_value="plan"),
        patch.object(graph, "research", return_value="research"),
        patch.object(graph, "draft", return_value="draft"),
        patch.object(graph, "review", return_value="review"),
    ):
        Agent.return_value.return_value = {"slides": []}
        flow = build_graph(mode="overlay")
        result = flow.run("topic")
        assert result["messages"][-1] == json.dumps({"slides": []})
        Agent.assert_called_once()
        Agent.return_value.assert_called_once_with("draft", "review")


def test_graph_nodes_are_traceable(monkeypatch):
    """All nodes should be decorated with LangSmith traceable."""
    recorded: list[str] = []

    def fake_traceable(fn):
        recorded.append(fn.__name__)
        return fn

    monkeypatch.setattr(graph.run_helpers, "traceable", fake_traceable)
    with (
        patch("app.graph.OverlayAgent") as Agent,
        patch.object(graph, "plan", return_value="plan"),
        patch.object(graph, "research", return_value="research"),
        patch.object(graph, "draft", return_value="draft"),
        patch.object(graph, "review", return_value="review"),
    ):
        Agent.return_value.return_value = "ov"
        build_graph(mode="overlay")
    expected = {
        "plan_node",
        "research_node",
        "draft_node",
        "review_node",
        "overlay_node",
    }
    assert expected.issubset(recorded)


def test_overlay_node_logs_metrics():
    """Overlay node should log token metrics via _log_metrics."""
    with (
        patch("app.graph.OverlayAgent") as Agent,
        patch.object(graph, "plan", return_value="plan"),
        patch.object(graph, "research", return_value="research"),
        patch.object(graph, "draft", return_value="draft"),
        patch.object(graph, "review", return_value="review"),
        patch.object(graph, "_log_metrics") as log,
    ):
        Agent.return_value.return_value = "ov text"
        flow = build_graph(mode="overlay")
        flow.run("topic")
        log.assert_any_call("ov text", 0)


def test_graph_with_primary_agent():
    """build_graph should delegate steps to a PrimaryAgent when provided."""
    primary = PrimaryAgent()
    with (
        patch.object(primary, "plan", return_value="plan") as plan_mock,
        patch.object(primary, "research", return_value="research") as research_mock,
        patch.object(primary, "draft", return_value="draft") as draft_mock,
        patch.object(primary, "review", return_value="final") as review_mock,
    ):
        flow = build_graph(primary=primary)
        result = flow.run("topic")
        assert result["output"] == "final"
    plan_mock.assert_called_once_with("topic", loop=0)
    research_mock.assert_called_once_with("plan", loop=0)
    draft_mock.assert_called_once_with("research", loop=0)
    review_mock.assert_called_once_with("draft", loop=0)
