import logging
import sys
from types import ModuleType, SimpleNamespace


def test_main_logs_stream_boundaries(monkeypatch, caplog):
    fake_agents = ModuleType("agents")
    fake_cw = ModuleType("agents.content_weaver")
    fake_streaming = ModuleType("agents.streaming")

    async def fake_run_content_weaver(state):
        return SimpleNamespace()

    fake_cw.run_content_weaver = fake_run_content_weaver
    fake_agents.content_weaver = fake_cw

    def fake_stream_messages(message: str) -> None:
        logging.getLogger("agents.streaming").info("[messages] %s", message)

    fake_streaming.stream_messages = fake_stream_messages
    fake_agents.streaming = fake_streaming
    sys.modules["agents"] = fake_agents
    sys.modules["agents.content_weaver"] = fake_cw
    sys.modules["agents.streaming"] = fake_streaming

    fake_core = ModuleType("core")
    fake_state = ModuleType("core.state")

    class State:  # type: ignore[too-few-public-methods]
        def __init__(self, prompt: str):
            self.prompt = prompt

    fake_state.State = State
    fake_core.state = fake_state
    sys.modules["core"] = fake_core
    sys.modules["core.state"] = fake_state

    from cli import generate_lecture

    async def fake_generate(topic: str):
        return {"result": "ok"}

    def fake_parse_args():
        return SimpleNamespace(topic="demo", verbose=True)

    monkeypatch.setattr(generate_lecture, "_generate", fake_generate)
    monkeypatch.setattr(generate_lecture, "parse_args", fake_parse_args)

    with caplog.at_level(logging.INFO):
        generate_lecture.main()

    assert "[messages] LLM response stream start" in caplog.text
    assert '[messages] LLM response stream complete: {"result": "ok"}' in caplog.text
