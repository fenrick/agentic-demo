"""Streaming endpoints exposing LangGraph updates by channel."""

from __future__ import annotations

from fastapi import APIRouter, Request  # type: ignore[import-not-found]
from sse_starlette.sse import EventSourceResponse  # type: ignore[import-not-found]

from web.sse import stream_workspace_events  # type: ignore[import-not-found]

router = APIRouter()


@router.get("/stream/{workspace}/state", response_model=None)
async def stream_state(request: Request, workspace: str) -> EventSourceResponse:
    """Stream state snapshot events for ``workspace``."""

    return EventSourceResponse(
        stream_workspace_events(workspace, "state", graph=request.app.state.graph)
    )


@router.get("/stream/{workspace}/actions", response_model=None)
async def stream_actions(request: Request, workspace: str) -> EventSourceResponse:
    """Stream action log events for ``workspace``."""

    return EventSourceResponse(
        stream_workspace_events(workspace, "action", graph=request.app.state.graph)
    )


@router.get("/stream/{workspace}/citations", response_model=None)
async def stream_citations(request: Request, workspace: str) -> EventSourceResponse:
    """Stream citation events for ``workspace``."""

    return EventSourceResponse(
        stream_workspace_events(workspace, "citation", graph=request.app.state.graph)
    )
