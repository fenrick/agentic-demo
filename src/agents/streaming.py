"""Utilities for emitting LangGraph stream events with safe fallbacks."""

from __future__ import annotations

import logging
from typing import Any, Callable


_logger = logging.getLogger(__name__)

# Attempt to import the optional ``langgraph_sdk`` stream helper once at module
# import time. This avoids repeatedly raising (and logging) an ``ImportError``
# for every streamed token when the dependency is absent or the API has
# changed.
try:  # pragma: no cover - optional dependency
    from langgraph_sdk import stream as _sdk_stream  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _sdk_stream = None
    _logger.debug(
        "langgraph_sdk stream function not available; falling back to logging",
        exc_info=True,
    )


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

    handler = fallback or _log_fallback

    if _sdk_stream is None:
        handler(channel, payload)
        return

    try:  # pragma: no cover - optional dependency
        _sdk_stream(channel, payload)
    except Exception:  # pragma: no cover - optional dependency
        _logger.debug("Streaming via langgraph_sdk failed", exc_info=True)
        handler(channel, payload)


def stream_messages(token: str) -> None:
    """Forward ``token`` over the ``messages`` channel."""

    stream("messages", token)


def stream_debug(message: str) -> None:
    """Forward ``message`` over the ``debug`` channel."""

    stream("debug", message)


__all__ = ["stream", "stream_messages", "stream_debug"]
