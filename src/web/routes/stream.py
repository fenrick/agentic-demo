"""Streaming endpoints exposing orchestrator channels via SSE."""

from __future__ import annotations

from fastapi import APIRouter, Request  # type: ignore[import-not-found]
from sse_starlette.sse import EventSourceResponse  # type: ignore[import-not-found]

from web.sse import stream_events  # type: ignore[import-not-found]

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
