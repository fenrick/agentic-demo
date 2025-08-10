"""Utilities for Server-Sent Events streaming."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

from fastapi import Request  # type: ignore[import-not-found]

from agents.streaming import subscribe
from web.schemas.sse import SseEvent  # type: ignore[import-not-found]
from web.telemetry import SSE_CLIENTS


async def stream_events(
    channel: str, request: Request
) -> AsyncGenerator[dict[str, Any], None]:
    """Yield events from ``channel`` as Server-Sent Events."""
    SSE_CLIENTS.add(1)
    try:
        async for payload in subscribe(channel):
            if await request.is_disconnected():
                break
            event = SseEvent(
                type=channel,
                payload=payload,
                timestamp=datetime.now(timezone.utc),
            )
            yield {"event": channel, "data": event.model_dump_json()}
    finally:
        SSE_CLIENTS.add(-1)


async def stream_workspace_events(
    workspace_id: str, event_type: str, request: Request
) -> AsyncGenerator[dict[str, Any], None]:
    """Yield workspace ``event_type`` updates as SSE events."""
    channel = f"{workspace_id}:{event_type}"
    SSE_CLIENTS.add(1)
    try:
        async for payload in subscribe(channel):
            if await request.is_disconnected():
                break
            event = SseEvent(
                type=event_type,
                payload=payload,
                timestamp=datetime.now(timezone.utc),
            )
            yield {"event": event_type, "data": event.model_dump_json()}
    finally:
        SSE_CLIENTS.add(-1)


__all__ = ["stream_events", "stream_workspace_events"]
