import asyncio
import logging

import pytest

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


@pytest.mark.asyncio
async def test_stream_broadcasts_to_subscribers() -> None:
    async def reader():
        async for payload in streaming.subscribe("test"):
            return payload

    task = asyncio.create_task(reader())
    await asyncio.sleep(0)
    streaming.stream("test", "payload")
    result = await asyncio.wait_for(task, 1)
    assert result == "payload"
