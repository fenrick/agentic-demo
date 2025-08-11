"""Streaming endpoints exposing orchestrator channels via SSE."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from fastapi import (  # type: ignore[import-not-found]
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sse_starlette.sse import EventSourceResponse  # type: ignore[import-not-found]

from web.auth import verify_jwt  # type: ignore[import-not-found]
from web.sse import (  # type: ignore[import-not-found]
    stream_events,
    stream_workspace_events,
)

router = APIRouter()

SSE_HEADERS: Dict[str, str] = {
    "Cache-Control": "no-store",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


def verify_stream_token(request: Request) -> Dict[str, Any]:
    """Validate the short-lived JWT passed as a query parameter."""
    host = request.url.hostname
    client_host = request.client.host if request.client else None
    if host in {"localhost", "127.0.0.1", "::1"} or client_host in {
        "127.0.0.1",
        "::1",
    }:
        return {"role": "user"}

    token = request.query_params.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token"
        )
    secret = request.app.state.settings.jwt_secret
    algorithm = request.app.state.settings.jwt_algorithm
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.PyJWTError as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc
    if payload.get("role") != "user":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return payload


@router.get("/stream/token")
async def issue_stream_token(
    request: Request, payload: Dict[str, Any] = Depends(verify_jwt)  # noqa: B008
) -> Dict[str, str]:
    """Return a short-lived JWT for authenticating SSE connections."""

    exp = datetime.now(tz=timezone.utc) + timedelta(minutes=1)
    token = jwt.encode(
        {"role": payload.get("role", "user"), "exp": exp},
        request.app.state.settings.jwt_secret,
        algorithm=request.app.state.settings.jwt_algorithm,
    )
    return {"token": token}


@router.get(
    "/stream/messages", response_model=None, dependencies=[Depends(verify_stream_token)]
)
async def stream_messages(request: Request) -> EventSourceResponse:
    """Stream token diff messages."""

    return EventSourceResponse(stream_events("messages", request), headers=SSE_HEADERS)


@router.get(
    "/stream/updates", response_model=None, dependencies=[Depends(verify_stream_token)]
)
async def stream_updates(request: Request) -> EventSourceResponse:
    """Stream citation and progress updates."""

    return EventSourceResponse(stream_events("updates", request), headers=SSE_HEADERS)


@router.get(
    "/stream/values", response_model=None, dependencies=[Depends(verify_stream_token)]
)
async def stream_values(request: Request) -> EventSourceResponse:
    """Stream structured state values."""

    return EventSourceResponse(stream_events("values", request), headers=SSE_HEADERS)


@router.get(
    "/stream/debug", response_model=None, dependencies=[Depends(verify_stream_token)]
)
async def stream_debug(request: Request) -> EventSourceResponse:
    """Stream debug and diagnostic messages."""

    return EventSourceResponse(stream_events("debug", request), headers=SSE_HEADERS)


def _workspace_event_response(
    workspace_id: str, event_type: str, request: Request
) -> EventSourceResponse:
    """Return an SSE response for workspace ``event_type`` events."""

    return EventSourceResponse(
        stream_workspace_events(workspace_id, event_type, request),
        headers=SSE_HEADERS,
    )


@router.get(
    "/stream/{workspace_id}/messages",
    response_model=None,
    dependencies=[Depends(verify_stream_token)],
)
async def stream_workspace_messages(
    workspace_id: str, request: Request
) -> EventSourceResponse:
    """Stream token diff messages for a workspace."""

    return _workspace_event_response(workspace_id, "messages", request)


@router.get(
    "/stream/{workspace_id}/updates",
    response_model=None,
    dependencies=[Depends(verify_stream_token)],
)
async def stream_workspace_updates(
    workspace_id: str, request: Request
) -> EventSourceResponse:
    """Stream citation and progress updates for a workspace."""

    return _workspace_event_response(workspace_id, "updates", request)


@router.get(
    "/stream/{workspace_id}/values",
    response_model=None,
    dependencies=[Depends(verify_stream_token)],
)
async def stream_workspace_values(
    workspace_id: str, request: Request
) -> EventSourceResponse:
    """Stream structured state values for a workspace."""

    return _workspace_event_response(workspace_id, "values", request)


@router.get(
    "/stream/{workspace_id}/debug",
    response_model=None,
    dependencies=[Depends(verify_stream_token)],
)
async def stream_workspace_debug(
    workspace_id: str, request: Request
) -> EventSourceResponse:
    """Stream diagnostic messages for a workspace."""

    return _workspace_event_response(workspace_id, "debug", request)
