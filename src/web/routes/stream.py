"""Streaming endpoints exposing orchestrator channels via SSE."""

from __future__ import annotations

from fastapi import APIRouter, Request  # type: ignore[import-not-found]
from sse_starlette.sse import EventSourceResponse  # type: ignore[import-not-found]

from web.sse import (  # type: ignore[import-not-found]
    stream_events,
    stream_workspace_events,
)

router = APIRouter()


@router.get("/stream/messages", response_model=None)
async def stream_messages(request: Request) -> EventSourceResponse:
    """Stream token diff messages."""

    return EventSourceResponse(stream_events("messages", request))


@router.get("/stream/updates", response_model=None)
async def stream_updates(request: Request) -> EventSourceResponse:
    """Stream citation and progress updates."""

    return EventSourceResponse(stream_events("updates", request))


@router.get("/stream/values", response_model=None)
async def stream_values(request: Request) -> EventSourceResponse:
    """Stream structured state values."""

    return EventSourceResponse(stream_events("values", request))


@router.get("/stream/debug", response_model=None)
async def stream_debug(request: Request) -> EventSourceResponse:
    """Stream debug and diagnostic messages."""

    return EventSourceResponse(stream_events("debug", request))


def _workspace_event_response(
    workspace_id: str, event_type: str, request: Request
) -> EventSourceResponse:
    """Return an SSE response for workspace ``event_type`` events."""

    return EventSourceResponse(
        stream_workspace_events(workspace_id, event_type, request)
    )


@router.get("/stream/{workspace_id}/messages", response_model=None)
async def stream_workspace_messages(
    workspace_id: str, request: Request
) -> EventSourceResponse:
    """Stream token diff messages for a workspace."""

    return _workspace_event_response(workspace_id, "messages", request)


@router.get("/stream/{workspace_id}/updates", response_model=None)
async def stream_workspace_updates(
    workspace_id: str, request: Request
) -> EventSourceResponse:
    """Stream citation and progress updates for a workspace."""

    return _workspace_event_response(workspace_id, "updates", request)


@router.get("/stream/{workspace_id}/values", response_model=None)
async def stream_workspace_values(
    workspace_id: str, request: Request
) -> EventSourceResponse:
    """Stream structured state values for a workspace."""

    return _workspace_event_response(workspace_id, "values", request)


@router.get("/stream/{workspace_id}/debug", response_model=None)
async def stream_workspace_debug(
    workspace_id: str, request: Request
) -> EventSourceResponse:
    """Stream diagnostic messages for a workspace."""

    return _workspace_event_response(workspace_id, "debug", request)
