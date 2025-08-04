"""Utilities for Server-Sent Events streaming."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

try:  # pragma: no cover - imported for side effects
    from core.orchestrator import graph  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - missing optional dependency
    graph = None

from web.schemas.sse import SseEvent  # type: ignore[import-not-found]


async def stream_workspace_events(
    workspace_id: str,
    event_type: str,
) -> AsyncGenerator[dict[str, Any], None]:
    """Yield filtered LangGraph updates as SSE events.

    Parameters
    ----------
    workspace_id:
        Identifier for the workspace whose events should be streamed.
    event_type:
        The event category to forward (``"state"``, ``"action"`` or ``"citation"``).
    """

    if graph is None:  # pragma: no cover - sanity guard
        return

    async for update in graph.astream(
        {}, config={"configurable": {"thread_id": workspace_id}}
    ):
        if update.get("type") != event_type:
            # Only forward updates matching the requested channel.
            continue

        event = SseEvent(
            type=event_type,
            payload=update.get("payload", update),
            timestamp=datetime.now(timezone.utc),
        )
        # ``event`` field allows clients to subscribe to specific SSE types.
        yield {"event": event_type, "data": event.model_dump_json()}
