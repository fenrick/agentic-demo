"""Polling endpoints for retrieving latest streamed events."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Response

from agents.streaming import get_latest
from web.schemas.sse import SseEvent

router = APIRouter(prefix="/poll")


def _event(channel: str, payload: object) -> SseEvent:
    return SseEvent(type=channel, payload=payload, timestamp=datetime.now(timezone.utc))


@router.get("/{event_type}", response_model=SseEvent | None)
async def poll_event(event_type: str):
    """Return the latest global ``event_type`` payload or ``204`` if absent."""

    payload = get_latest(event_type)
    if payload is None:
        return Response(status_code=204)
    return _event(event_type, payload)


@router.get("/{workspace_id}/{event_type}", response_model=SseEvent | None)
async def poll_workspace_event(workspace_id: str, event_type: str):
    """Return latest workspace event or ``204`` if none available."""

    channel = f"{workspace_id}:{event_type}"
    payload = get_latest(channel)
    if payload is None:
        return Response(status_code=204)
    return _event(event_type, payload)
