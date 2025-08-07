"""Utilities for emitting orchestrator stream events."""

from __future__ import annotations

from typing import Any, Callable


def stream(
    channel: str,
    payload: Any,
    *,
    fallback: Callable[[str, Any], None] | None = None,
) -> None:
    """Send ``payload`` to ``channel`` using ``fallback`` if provided."""

    if fallback:
        fallback(channel, payload)


def stream_messages(token: str) -> None:
    """Forward ``token`` over the ``messages`` channel."""

    stream("messages", token)


def stream_debug(message: str) -> None:
    """Forward ``message`` over the ``debug`` channel."""

    stream("debug", message)


__all__ = ["stream", "stream_messages", "stream_debug"]
