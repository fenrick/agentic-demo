"""Utilities for emitting LangGraph stream events with safe fallbacks."""

from __future__ import annotations

import logging
from typing import Any


def stream(channel: str, payload: Any) -> None:
    """Send ``payload`` to ``channel`` if ``langgraph_sdk`` is installed.

    Falls back to printing when the optional dependency is missing or raises
    an exception.
    """

    try:
        from langgraph_sdk import stream as _stream  # type: ignore

        _stream(channel, payload)
    except Exception:  # pragma: no cover - optional dependency
        logging.exception("Streaming via langgraph_sdk failed")
        if channel == "messages":
            print(payload, end="", flush=True)
        else:
            print(payload, flush=True)


def stream_messages(token: str) -> None:
    """Forward ``token`` over the ``messages`` channel."""

    stream("messages", token)


def stream_debug(message: str) -> None:
    """Forward ``message`` over the ``debug`` channel."""

    stream("debug", message)


__all__ = ["stream", "stream_messages", "stream_debug"]
