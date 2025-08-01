from unittest.mock import patch

import asyncio
import pytest

from app.agents import ChatAgent

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
