"""Utilities for Server-Sent Events streaming."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

from core.orchestrator import build_main_flow
from core.state import State
from web.schemas.sse import SseEvent  # type: ignore[import-not-found]


async def stream_workspace_events(
    workspace_id: str, event_type: str
) -> AsyncGenerator[dict[str, Any], None]:
    """Yield filtered pipeline updates as SSE events."""

    state = State(workspace_id=workspace_id)

    async def _generate() -> AsyncGenerator[dict[str, Any], None]:
        flow = build_main_flow()
        lookup = {n.name: n for n in flow}
        current = flow[0]
        while current:
            action_event = {"type": "action", "payload": current.name}
            if action_event["type"] == event_type:
                yield action_event
            result = await current.fn(state)
            state_event = {"type": "state", "payload": state.to_dict()}
            if state_event["type"] == event_type:
                yield state_event
            next_name = current.next
            if current.condition is not None:
                next_name = current.condition(result, state)
            if next_name is None:
                break
            current = lookup[next_name]

    async for update in _generate():
        event = SseEvent(
            type=event_type,
            payload=update.get("payload", update),
            timestamp=datetime.now(timezone.utc),
        )
        yield {"event": event_type, "data": event.model_dump_json()}


__all__ = ["stream_workspace_events"]
