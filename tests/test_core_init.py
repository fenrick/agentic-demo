import logging

from core import Agent, get_logger


class DummyAgent(Agent):
    def act(self, message: str, /, **kwargs: object) -> str:
        return message.upper()


def test_agent_act_returns_uppercase():
    agent = DummyAgent("dummy")
    assert agent.act("hi") == "HI"


def test_get_logger_matches_name():
    logger = get_logger("sample")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "sample"
