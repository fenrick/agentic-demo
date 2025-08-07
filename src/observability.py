"""Logfire configuration and instrumentation helpers."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import logfire
from loguru import logger as loguru_logger

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from fastapi import FastAPI


def init_observability() -> None:
    """Configure Logfire and instrument global libraries.

    Reads configuration from environment variables so that instrumentation
    occurs before the application's settings module is imported.
    """
    token = os.getenv("LOGFIRE_API_KEY")
    project = os.getenv("LOGFIRE_PROJECT")

    logfire.configure(token=token, service_name=project)
    logging.getLogger().addHandler(logfire.LogfireLoggingHandler())
    logfire.instrument_pydantic()
    logfire.instrument_httpx()
    logfire.instrument_sqlalchemy()
    logfire.instrument_sqlite3()
    logfire.instrument_system_metrics()
    loguru_logger.add(logfire.loguru_handler())


def instrument_app(app: "FastAPI") -> None:
    """Instrument a FastAPI application and its ASGI server."""
    logfire.instrument_fastapi(app, capture_headers=True)
    logfire.instrument_asgi(app)
