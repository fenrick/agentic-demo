"""Utilities for Server-Sent Events streaming."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from fastapi import Request  # type: ignore[import-not-found]
from web.schemas.sse import SseEvent  # type: ignore[import-not-found]

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    from langgraph.graph.state import CompiledStateGraph  # type: ignore[import-not-found]
else:  # pragma: no cover - dependency optional at runtime
    CompiledStateGraph = Any  # type: ignore[misc, assignment]


async def stream_workspace_events(
    workspace_id: str,
    event_type: str,
    graph: CompiledStateGraph | None = None,
    request: Request | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """Yield filtered LangGraph updates as SSE events.

    Parameters
    ----------
    workspace_id:
        Identifier for the workspace whose events should be streamed.
    event_type:
        The event category to forward (``"state"``, ``"action"`` or ``"citation"``).
    """

    if graph is None and request is not None:
        graph = getattr(request.app.state, "graph", None)

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
