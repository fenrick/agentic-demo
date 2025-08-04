"""Streaming endpoints exposing LangGraph updates by channel."""

from __future__ import annotations

from fastapi import APIRouter  # type: ignore[import-not-found]
from sse_starlette.sse import EventSourceResponse  # type: ignore[import-not-found]

from web.sse import stream_workspace_events  # type: ignore[import-not-found]

router = APIRouter()


@router.get("/stream/{workspace}/state", response_model=None)
async def stream_state(workspace: str) -> EventSourceResponse:
    """Stream state snapshot events for ``workspace``."""

    return EventSourceResponse(stream_workspace_events(workspace, "state"))


@router.get("/stream/{workspace}/actions", response_model=None)
async def stream_actions(workspace: str) -> EventSourceResponse:
    """Stream action log events for ``workspace``."""

    return EventSourceResponse(stream_workspace_events(workspace, "action"))


@router.get("/stream/{workspace}/citations", response_model=None)
async def stream_citations(workspace: str) -> EventSourceResponse:
    """Stream citation events for ``workspace``."""

    return EventSourceResponse(stream_workspace_events(workspace, "citation"))
