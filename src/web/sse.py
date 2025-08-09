"""Utilities for Server-Sent Events streaming."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

from agents.streaming import subscribe
from web.schemas.sse import SseEvent  # type: ignore[import-not-found]


async def stream_workspace_events(
    workspace_id: str, event_type: str
) -> AsyncGenerator[dict[str, Any], None]:
    """Yield workspace ``event_type`` updates as SSE events."""

    channel = f"{workspace_id}:{event_type}"
    async for payload in subscribe(channel):
        event = SseEvent(
            type=event_type,
            payload=payload,
            timestamp=datetime.now(timezone.utc),
        )
        yield {"event": event_type, "data": event.model_dump_json()}


__all__ = ["stream_workspace_events"]
