from unittest.mock import patch

from app.primary_agent import PrimaryAgent


def test_primary_agent_uses_gpt41():
    pa = PrimaryAgent()
    assert pa.agent.model == "gpt-4.1"


def test_primary_agent_delegates_calls():
    pa = PrimaryAgent()
    with (
        patch("app.primary_agent._plan", return_value="p") as plan_mock,
        patch("app.primary_agent._research", return_value="r") as research_mock,
        patch("app.primary_agent._draft", return_value="d") as draft_mock,
        patch("app.primary_agent._review", return_value="v") as review_mock,
    ):
        assert pa.plan("t", loop=1) == "p"
        assert pa.research("o", loop=2) == "r"
        assert pa.draft("n", loop=3) == "d"
        assert pa.review("x", loop=4) == "v"
    plan_mock.assert_called_once_with("t", agent=pa.agent, loop=1)
    research_mock.assert_called_once_with("o", agent=pa.agent, loop=2)
    draft_mock.assert_called_once_with("n", agent=pa.agent, loop=3)
    review_mock.assert_called_once_with("x", agent=pa.agent, loop=4)
