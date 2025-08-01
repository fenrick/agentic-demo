from unittest.mock import patch

from app.graph import build_graph
from app.agents import ChatAgent


def test_graph_flow():
    with patch.object(ChatAgent, "__call__", return_value="done") as mock_call:
        graph = build_graph()
        result = graph.run("hello")
        mock_call.assert_called_once()
        assert result["output"] == "done"
        assert result["messages"][-1]["content"] == "done"
