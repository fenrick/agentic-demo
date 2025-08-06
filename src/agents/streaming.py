"""Utilities for emitting LangGraph stream events with safe fallbacks."""

from __future__ import annotations

import logging
from typing import Any, Callable


_logger = logging.getLogger(__name__)


def _log_fallback(channel: str, payload: Any) -> None:
    """Log ``payload`` tagged with ``channel``."""

    level = logging.DEBUG if channel == "debug" else logging.INFO
    _logger.log(level, "[%s] %s", channel, payload)


def stream(
    channel: str,
    payload: Any,
    *,
    fallback: Callable[[str, Any], None] | None = None,
) -> None:
    """Send ``payload`` to ``channel`` using ``langgraph_sdk`` if available.

    Falls back to ``fallback`` when the optional dependency is missing or raises
    an exception. The default fallback logs the payload and tags it with its
    ``channel``.

    Args:
        channel: Name of the stream channel (e.g., ``"messages"``, ``"debug"``).
        payload: Data to send.
        fallback: Optional callable invoked on failure. It receives ``channel``
            and ``payload``.
    """

    try:
        from langgraph_sdk import stream as _stream  # type: ignore

        _stream(channel, payload)
    except Exception:  # pragma: no cover - optional dependency
        _logger.exception("Streaming via langgraph_sdk failed")
        handler = fallback or _log_fallback
        handler(channel, payload)


def stream_messages(token: str) -> None:
    """Forward ``token`` over the ``messages`` channel."""

    stream("messages", token)


def stream_debug(message: str) -> None:
    """Forward ``message`` over the ``debug`` channel."""

    stream("debug", message)


__all__ = ["stream", "stream_messages", "stream_debug"]
