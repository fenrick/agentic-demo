"""Utilities for emitting and subscribing to orchestrator stream events."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any, Callable, DefaultDict, List

_SUBSCRIBERS: DefaultDict[str, List[asyncio.Queue[Any]]] = defaultdict(list)


def stream(
    channel: str,
    payload: Any,
    *,
    fallback: Callable[[str, Any], None] | None = None,
) -> None:
    """Send ``payload`` to ``channel``.

    Parameters
    ----------
    channel:
        Destination channel name.
    payload:
        Payload to broadcast to subscribers.
    fallback:
        Optional callable invoked with ``channel`` and ``payload`` if provided.
    """

    for queue in list(_SUBSCRIBERS.get(channel, [])):
        queue.put_nowait(payload)
    if fallback:
        fallback(channel, payload)


async def subscribe(channel: str) -> AsyncIterator[Any]:
    """Yield payloads published to ``channel`` until cancelled."""

    queue: asyncio.Queue[Any] = asyncio.Queue()
    _SUBSCRIBERS[channel].append(queue)
    try:
        while True:
            yield await queue.get()
    finally:
        _SUBSCRIBERS[channel].remove(queue)


def stream_messages(token: str) -> None:
    """Forward ``token`` over the ``messages`` channel."""

    stream("messages", token)


def stream_debug(message: str) -> None:
    """Forward ``message`` over the ``debug`` channel."""

    stream("debug", message)


__all__ = ["stream", "subscribe", "stream_messages", "stream_debug"]
