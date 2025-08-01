from unittest.mock import patch, MagicMock

from app.document_dag import DocumentDAG
from app.primary_agent import PrimaryAgent


def test_parse_outline_basic():
    wf = DocumentDAG()
    outline = "- Intro\n- Body\n- Conclusion"
    assert wf.parse_outline(outline) == ["Intro", "Body", "Conclusion"]


def test_parse_outline_numbers_and_markdown():
    wf = DocumentDAG()
    outline = "1. Intro\n1.1 Details\n## Conclusion"
    assert wf.parse_outline(outline) == ["Intro", "Details", "Conclusion"]


def test_generate_document_runs_graph_per_heading():
    wf = DocumentDAG()
    with (
        patch("app.document_dag.agents.plan", return_value="- A\n- B") as plan_mock,
        patch("app.document_dag.agents.review", return_value="final") as review_mock,
        patch("app.document_dag.build_graph") as build_mock,
    ):
        mock_graph = MagicMock()
        mock_graph.run.side_effect = [
            {"output": "secA"},
            {"output": "secB"},
        ]
        build_mock.return_value = mock_graph
        result = wf.generate("topic")
        plan_mock.assert_called_once_with("topic")
        build_mock.assert_called_once_with(wf.overlay, primary=None, skip_plan=True)
        assert result == "final"
        review_mock.assert_called_once_with("secA\n\nsecB")
        assert mock_graph.run.call_count == 2


def test_workflow_uses_primary_agent():
    wf = DocumentDAG(primary=PrimaryAgent())
    with (
        patch.object(wf.primary, "plan", return_value="- A\n- B") as plan_mock,
        patch.object(wf.primary, "review", return_value="final") as review_mock,
        patch("app.document_dag.build_graph") as build_mock,
    ):
        mock_graph = MagicMock()
        mock_graph.run.side_effect = [
            {"output": "secA"},
            {"output": "secB"},
        ]
        build_mock.return_value = mock_graph
        result = wf.generate("topic")
    plan_mock.assert_called_once_with("topic")
    build_mock.assert_called_once_with(wf.overlay, primary=wf.primary, skip_plan=True)
    review_mock.assert_called_once_with("secA\n\nsecB")
    assert result == "final"
