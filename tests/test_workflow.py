from unittest.mock import patch, MagicMock

from app.workflow import DocumentWorkflow


def test_parse_outline_basic():
    wf = DocumentWorkflow()
    outline = "- Intro\n- Body\n- Conclusion"
    assert wf.parse_outline(outline) == ["Intro", "Body", "Conclusion"]


def test_parse_outline_numbers_and_markdown():
    wf = DocumentWorkflow()
    outline = "1. Intro\n1.1 Details\n## Conclusion"
    assert wf.parse_outline(outline) == ["Intro", "Details", "Conclusion"]


def test_generate_document_runs_graph_per_heading():
    wf = DocumentWorkflow()
    with (
        patch("app.workflow.agents.plan", return_value="- A\n- B") as plan_mock,
        patch("app.workflow.agents.review", return_value="final") as review_mock,
        patch("app.workflow.build_graph") as build_mock,
    ):
        mock_graph = MagicMock()
        mock_graph.run.side_effect = [
            {"output": "secA"},
            {"output": "secB"},
        ]
        build_mock.return_value = mock_graph
        result = wf.generate("topic")
        plan_mock.assert_called_once_with("topic")
        build_mock.assert_called_once_with(wf.overlay, skip_plan=True)
        assert result == "final"
        review_mock.assert_called_once_with("secA\n\nsecB")
        assert mock_graph.run.call_count == 2
