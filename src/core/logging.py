"""Centralised configuration for JSON logging and request correlation.

This module configures `loguru` to emit structured JSON logs and exposes
helpers for binding contextual information. A FastAPI middleware is provided
to attach a short request identifier to each incoming request so log entries
can be correlated across services.
"""

from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Optional

from loguru import logger as _logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Context variable storing the request ID for the current execution context.
_REQUEST_ID_CTX: ContextVar[str | None] = ContextVar("request_id", default=None)


class InterceptHandler(logging.Handler):
    """Redirect standard logging records to Loguru."""

    def emit(
        self, record: logging.LogRecord
    ) -> None:  # pragma: no cover - thin wrapper
        try:
            level = _logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        _logger.bind(request_id=_REQUEST_ID_CTX.get()).opt(
            depth=2, exception=record.exc_info
        ).log(level, record.getMessage())


def configure_logging(level: str = "INFO") -> None:
    """Configure Loguru to produce JSON structured logs.

    Args:
        level: Minimum log level to emit. Defaults to ``"INFO"``.
    """

    _logger.remove()
    _logger.add(sys.stdout, level=level, serialize=True)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


def get_logger(job_id: Optional[str] = None, user_id: Optional[str] = None):
    """Return a logger bound with job, user and request identifiers.

    Args:
        job_id: Identifier for the current job or workspace.
        user_id: Identifier for the acting user.

    Returns:
        ``loguru.Logger`` instance bound with the provided IDs.
    """

    return _logger.bind(
        job_id=job_id, user_id=user_id, request_id=_REQUEST_ID_CTX.get()
    )


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a short request ID to every HTTP request."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = uuid.uuid4().hex[:8]
        request.state.req_id = request_id
        token = _REQUEST_ID_CTX.set(request_id)
        try:
            response = await call_next(request)
        finally:
            _REQUEST_ID_CTX.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response


# Export the base logger for modules that don't require additional context.
logger = _logger
