from app.agents import ChatAgent
from unittest.mock import patch


def test_chat_agent_calls_openai():
    agent = ChatAgent()
    messages = [{"role": "user", "content": "hi"}]
    with patch("openai.ChatCompletion.create") as mock_create:
        mock_create.return_value = {
            "choices": [{"message": {"content": "hello"}}]
        }
        assert agent(messages) == "hello"
        mock_create.assert_called_once_with(model=agent.model, messages=messages)
