import logging
import sys
from types import SimpleNamespace

from agents import streaming


def test_stream_uses_sdk(monkeypatch):
    calls = []

    def fake_stream(channel: str, payload: str) -> None:
        calls.append((channel, payload))

    monkeypatch.setitem(
        sys.modules, "langgraph_sdk", SimpleNamespace(stream=fake_stream)
    )
    streaming.stream("messages", "hello")
    assert calls == [("messages", "hello")]


def test_stream_logs_on_failure(monkeypatch, caplog):
    def failing_stream(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setitem(
        sys.modules, "langgraph_sdk", SimpleNamespace(stream=failing_stream)
    )
    with caplog.at_level(logging.DEBUG):
        streaming.stream("messages", "hi")
        streaming.stream("debug", "dbg")

    assert "[messages] hi" in caplog.text
    assert "[debug] dbg" in caplog.text
