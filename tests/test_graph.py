from unittest.mock import patch

import asyncio
import pytest

from app.agents import ChatAgent
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
    from app.overlay_agent import OverlayAgent

    overlay = OverlayAgent(ChatAgent())
    with (
        patch.object(OverlayAgent, "__call__", return_value="ov") as ov_mock,
        patch.object(graph, "plan", return_value="plan"),
        patch.object(graph, "research", return_value="research"),
        patch.object(graph, "draft", return_value="draft"),
        patch.object(graph, "review", return_value="review"),
    ):
        flow = build_graph(overlay)
        result = flow.run("topic")
        assert result["output"] == "ov"
        ov_mock.assert_called_once_with("draft", "review")


@pytest.mark.asyncio
async def test_graph_async_overlay_dict():
    """Graph run should return a dict with slides or ai_overlay when overlay outputs one."""
    from app.overlay_agent import OverlayAgent

    overlay = OverlayAgent(ChatAgent())
    with (
        patch.object(OverlayAgent, "__call__", return_value={"slides": []}) as ov_mock,
        patch.object(graph, "plan", return_value="plan"),
        patch.object(graph, "research", return_value="research"),
        patch.object(graph, "draft", return_value="draft"),
        patch.object(graph, "review", return_value="review"),
    ):
        flow = build_graph(overlay)
        result = await asyncio.to_thread(flow.run, "topic")
        assert isinstance(result["output"], dict)
        assert "slides" in result["output"] or "ai_overlay" in result["output"]
        ov_mock.assert_called_once_with("draft", "review")


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
    from app.overlay_agent import OverlayAgent
    import json

    overlay = OverlayAgent(ChatAgent())
    with (
        patch.object(OverlayAgent, "__call__", return_value={"slides": []}),
        patch.object(graph, "plan", return_value="plan"),
        patch.object(graph, "research", return_value="research"),
        patch.object(graph, "draft", return_value="draft"),
        patch.object(graph, "review", return_value="review"),
    ):
        flow = build_graph(overlay)
        result = flow.run("topic")
        assert result["messages"][-1] == json.dumps({"slides": []})


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
