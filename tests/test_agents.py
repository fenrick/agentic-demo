import app
from app.agents import ChatAgent, plan, research, draft, review
from unittest.mock import patch, MagicMock


def test_chat_agent_calls_openai():
    agent = ChatAgent()
    messages = [{"role": "user", "content": "hi"}]
    with patch("app.agents.openai.ChatCompletion.create") as mock_create:
        mock_create.return_value = {"choices": [{"message": {"content": "hello"}}]}
        assert agent(messages) == "hello"
        mock_create.assert_called_once_with(model=agent.model, messages=messages)


def test_chat_agent_calls_responses_api_when_search_enabled():
    agent = ChatAgent(use_search=True)
    messages = [{"role": "user", "content": "hi"}]
    with patch.object(app.agents.openai, "Responses", create=True) as res:
        mock_create = res.create
        mock_create.return_value = {"choices": [{"message": {"content": "hello"}}]}
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


def test_agent_functions_use_yaml_templates():
    """Each agent function should render prompts from YAML files."""
    calls = []

    def fake_load(name):
        calls.append(name)
        return {
            "plan": "p {topic}",
            "research": "r {outline}",
            "draft": "d {notes}",
            "review": "v {text}",
            "system": "sys",
            "user": "{input}",
        }[name]

    with (
        patch("app.utils.load_prompt", side_effect=fake_load),
        patch.object(ChatAgent, "__call__", return_value="x") as mock,
    ):
        plan("topic")
        research("topic")
        draft("notes")
        review("text")

        assert mock.call_count == 4
        msgs = mock.call_args_list[0][0][0]
        assert msgs[0]["role"] == "system" and msgs[0]["content"] == "sys"
        assert msgs[1]["content"] == "p topic"
        for name in ["plan", "research", "draft", "review"]:
            assert name in calls


def test_chat_agent_falls_back_when_openai_unavailable():
    agent = ChatAgent()
    messages = [{"role": "user", "content": "hi"}]
    with patch(
        "app.agents.openai.ChatCompletion.create", side_effect=NotImplementedError
    ):
        assert agent(messages) == "OpenAI API unavailable"


def test_chat_agent_falls_back_when_responses_api_unavailable():
    agent = ChatAgent(use_search=True)
    with patch.object(app.agents.openai, "Responses", create=True) as res:
        res.create.side_effect = NotImplementedError
        assert (
            agent([{"role": "user", "content": "ignored"}]) == "OpenAI API unavailable"
        )


def test_chat_agent_custom_fallback_message():
    agent = ChatAgent(fallback="oops")
    with patch(
        "app.agents.openai.ChatCompletion.create", side_effect=NotImplementedError
    ):
        assert agent([{"role": "user", "content": "ignored"}]) == "oops"


def test_agent_functions_are_traceable():
    assert hasattr(plan, "__langsmith_traceable__")
    assert hasattr(research, "__langsmith_traceable__")
    assert hasattr(draft, "__langsmith_traceable__")
    assert hasattr(review, "__langsmith_traceable__")


def test_metrics_logged_during_calls():
    fake_run = MagicMock()
    with (
        patch("app.agents._call_agent", return_value="x [1]"),
        patch("app.agents.run_helpers.get_current_run_tree", return_value=fake_run),
        patch("app.agents.logger") as log,
    ):
        assert plan("topic", loop=1) == "x [1]"
        fake_run.add_event.assert_called_once()
        log.info.assert_called_once()
