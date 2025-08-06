import logging
import sys
from contextlib import asynccontextmanager
from types import ModuleType, SimpleNamespace


def test_main_logs_stream_boundaries(monkeypatch, caplog):
    fake_streaming = ModuleType("agents.streaming")

    def fake_stream_messages(message: str) -> None:
        logging.getLogger("agents.streaming").info("[messages] %s", message)

    fake_streaming.stream_messages = fake_stream_messages
    sys.modules["agents.streaming"] = fake_streaming

    fake_orchestrator = ModuleType("core.orchestrator")
    fake_orchestrator.graph = SimpleNamespace(
        ainvoke=lambda *_a, **_k: {"result": "ok"}
    )

    @asynccontextmanager
    async def fake_saver():
        yield object()

    fake_orchestrator.create_checkpoint_saver = fake_saver
    sys.modules["core.orchestrator"] = fake_orchestrator

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
