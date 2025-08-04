"""Utilities for Server-Sent Events streaming."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

try:  # pragma: no cover - imported for side effects
    from core.orchestrator import graph
except Exception:  # pragma: no cover - missing optional dependency
    graph = None

from web.schemas.sse import SseEvent


async def stream_workspace_events(
    workspace_id: str,
) -> AsyncGenerator[dict[str, Any], None]:
    """Yield LangGraph updates for ``workspace_id`` as SSE events."""
    if graph is None:  # pragma: no cover - sanity guard
        return
    async for update in graph.astream(
        {}, config={"configurable": {"thread_id": workspace_id}}
    ):
        event = SseEvent(
            type=update.get("type", "message"),
            payload=update.get("payload", update),
            timestamp=datetime.now(timezone.utc),
        )
        yield {"data": event.model_dump_json()}
