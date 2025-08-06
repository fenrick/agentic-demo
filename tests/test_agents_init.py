from agents import EchoAgent, ReverseAgent


def test_echo_agent_returns_same_message():
    agent = EchoAgent("echo")
    assert agent.act("hello") == "hello"


def test_reverse_agent_returns_reversed_message():
    agent = ReverseAgent("rev")
    assert agent.act("abc") == "cba"
