"""Utilities for emitting and subscribing to orchestrator stream events."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any, Callable, DefaultDict, Dict, List

_SUBSCRIBERS: DefaultDict[str, List[asyncio.Queue[Any]]] = defaultdict(list)
# Store the most recent payload for each channel so clients can poll updates.
_LATEST: Dict[str, Any] = {}


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

    # Persist the latest payload so that polling clients can retrieve it.
    _LATEST[channel] = payload

    for queue in list(_SUBSCRIBERS.get(channel, [])):
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:  # pragma: no cover - race condition
                pass
            queue.put_nowait(payload)
    if fallback:
        fallback(channel, payload)


async def subscribe(channel: str, *, max_queue: int = 100) -> AsyncIterator[Any]:
    """Yield payloads published to ``channel`` until cancelled.

    Parameters
    ----------
    channel:
        Name of the channel to subscribe to.
    max_queue:
        Maximum number of pending messages to retain before older messages are
        discarded. Defaults to ``100``.
    """

    queue: asyncio.Queue[Any] = asyncio.Queue(max_queue)
    _SUBSCRIBERS[channel].append(queue)
    try:
        while True:
            yield await queue.get()
    finally:
        _SUBSCRIBERS[channel].remove(queue)


def get_latest(channel: str) -> Any | None:
    """Return the most recent payload published to ``channel``."""

    return _LATEST.get(channel)


def stream_messages(token: str) -> None:
    """Forward ``token`` over the ``messages`` channel and log it."""

    stream("messages", token, fallback=_log_message)


def stream_debug(message: str) -> None:
    """Forward ``message`` over the ``debug`` channel and log it."""

    stream("debug", message, fallback=_log_debug)


def _log_message(_channel: str, payload: Any) -> None:
    """Emit ``payload`` to the logger as a ``messages`` event."""

    logging.getLogger(__name__).info("[messages] %s", payload)


def _log_debug(_channel: str, payload: Any) -> None:
    """Emit ``payload`` to the logger as a ``debug`` event."""

    logging.getLogger(__name__).debug("[debug] %s", payload)


__all__ = [
    "stream",
    "subscribe",
    "get_latest",
    "stream_messages",
    "stream_debug",
]
