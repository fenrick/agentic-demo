"""Health and readiness endpoints."""

from __future__ import annotations

import importlib.util

from fastapi import HTTPException, Request
from sqlalchemy import text


async def healthz(request: Request) -> dict[str, str]:
    """Verify the database connection is available."""

    try:
        async with request.app.state.db() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - error path
        raise HTTPException(status_code=500, detail="database unavailable") from exc
    return {"status": "ok"}


async def readyz(request: Request) -> dict[str, str]:
    """Check that critical dependencies are ready."""

    missing: list[str] = []
    if importlib.util.find_spec("logfire") is None:
        missing.append("logfire")
    if getattr(request.app.state, "research_client", None) is None:
        missing.append("research_client")
    if missing:
        raise HTTPException(status_code=500, detail={"missing": missing})
    return {"status": "ready"}
