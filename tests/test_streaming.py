import logging

from agents import streaming


def test_stream_uses_sdk(monkeypatch):
    calls = []

    def fake_stream(channel: str, payload: str) -> None:
        calls.append((channel, payload))

    monkeypatch.setattr(streaming, "_sdk_stream", fake_stream)
    streaming.stream("messages", "hello")
    assert calls == [("messages", "hello")]


def test_stream_logs_on_failure(monkeypatch, caplog):
    def failing_stream(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(streaming, "_sdk_stream", failing_stream)
    with caplog.at_level(logging.DEBUG):
        streaming.stream("messages", "hi")
        streaming.stream("debug", "dbg")

    assert "[messages] hi" in caplog.text
    assert "[debug] dbg" in caplog.text


def test_stream_without_sdk(monkeypatch, caplog):
    monkeypatch.setattr(streaming, "_sdk_stream", None)
    with caplog.at_level(logging.INFO):
        streaming.stream("messages", "hi")

    assert "[messages] hi" in caplog.text
