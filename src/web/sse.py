"""Utilities for Server-Sent Events streaming."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

from fastapi import Request  # type: ignore[import-not-found]

from core.orchestrator import Graph
from core.state import State
from web.schemas.sse import SseEvent  # type: ignore[import-not-found]


async def stream_workspace_events(
    workspace_id: str,
    event_type: str,
    graph: Graph | None = None,
    request: Request | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """Yield filtered graph updates as SSE events."""

    if graph is None and request is not None:
        graph = getattr(request.app.state, "graph", None)

    if graph is None:  # pragma: no cover - sanity guard
        return

    state = State(workspace_id=workspace_id)
    async for update in graph.stream(state):
        if update.get("type") != event_type:
            continue
        event = SseEvent(
            type=event_type,
            payload=update.get("payload", update),
            timestamp=datetime.now(timezone.utc),
        )
        yield {"event": event_type, "data": event.model_dump_json()}


__all__ = ["stream_workspace_events"]
