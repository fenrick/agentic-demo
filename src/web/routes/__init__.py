"""Route registration helpers."""

from __future__ import annotations

from fastapi import FastAPI

from .stream import router as stream_router


def register_sse_routes(app: FastAPI) -> None:
    """Backward-compatible helper to attach SSE routes to ``app``."""

    app.include_router(stream_router)


__all__ = ["register_sse_routes", "stream_router"]
