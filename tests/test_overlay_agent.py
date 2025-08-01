from app.overlay_agent import OverlayAgent
from app.agents import ChatAgent
from unittest.mock import patch


def test_overlay_agent_composes_prompt():
    with patch.object(ChatAgent, "__call__", return_value="result") as mock:
        agent = ChatAgent()
        oa = OverlayAgent(agent)
        out = oa("orig", "add")
        assert out == "result"
        assert mock.call_count == 1
        called_messages = mock.call_args[0][0]
        assert "orig" in called_messages[0]["content"]
        assert "add" in called_messages[0]["content"]


def test_overlay_agent_returns_dict_when_json():
    """__call__ should return a dict if the agent output is JSON."""
    json_response = '{"slides": []}'
    with patch.object(ChatAgent, "__call__", return_value=json_response):
        oa = OverlayAgent(ChatAgent())
        result = oa("orig", "add")
        assert isinstance(result, dict)
        assert result == {"slides": []}
