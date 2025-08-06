import logging

from agents import streaming


def test_stream_noop_without_fallback(caplog):
    with caplog.at_level(logging.INFO):
        streaming.stream("messages", "hi")

    assert caplog.text == ""


def test_stream_uses_fallback(caplog):
    def fallback(channel: str, payload: str) -> None:
        logging.getLogger("test").info("[%s] %s", channel, payload)

    with caplog.at_level(logging.INFO):
        streaming.stream("messages", "hi", fallback=fallback)

    assert "[messages] hi" in caplog.text
