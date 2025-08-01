from app.agents import ChatAgent, plan, research, draft, review
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


def test_plan_research_draft_review_calls_agent():
    with patch.object(ChatAgent, "__call__", return_value="x") as mock:
        agent = ChatAgent()
        assert plan("topic", agent=agent) == "x"
        assert research("plan", agent=agent) == "x"
        assert draft("research", agent=agent) == "x"
        assert review("draft", agent=agent) == "x"
        assert mock.call_count == 4
