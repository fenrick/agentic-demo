"""FastAPI routes for web components."""

from __future__ import annotations

from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse

from web.sse import stream_workspace_events


def register_sse_routes(app: FastAPI) -> None:
    """Attach SSE endpoints to ``app``."""

    @app.get("/stream/{workspace}", response_model=None)
    async def stream_events(workspace: str):
        return EventSourceResponse(stream_workspace_events(workspace))
