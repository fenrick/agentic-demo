"""Streaming endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from web.sse import stream_workspace_events

router = APIRouter()


@router.get("/stream/{workspace}", response_model=None)
async def stream_events(workspace: str) -> EventSourceResponse:
    """Stream LangGraph events for a workspace as Server Sent Events."""

    return EventSourceResponse(stream_workspace_events(workspace))
