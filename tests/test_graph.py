from unittest.mock import patch

from app.agents import ChatAgent

from app import graph
from app.graph import build_graph



def test_graph_flow():
    with (
        patch.object(graph, "plan", return_value="plan") as plan_mock,
        patch.object(graph, "research", return_value="research") as research_mock,
        patch.object(graph, "draft", return_value="draft") as draft_mock,
        patch.object(graph, "review", return_value="review") as review_mock,
    ):
        flow = build_graph()
        result = flow.run("topic")
        assert result["output"] == "review"
        assert plan_mock.called and research_mock.called
        assert draft_mock.called and review_mock.called

def test_graph_with_overlay():
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
        ov_mock.assert_called_once()
