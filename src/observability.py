"""Logfire configuration and instrumentation helpers."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, cast

import logfire
from loguru import logger as loguru_logger
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.metrics import get_meter_provider, set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from starlette.types import ASGIApp

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from fastapi import FastAPI


REPO_ROOT = Path(__file__).resolve().parents[1]
# Only trace modules that live under the repository's ``src`` directory.
SRC_DIR = REPO_ROOT / "src"

_prometheus_reader = PrometheusMetricReader()
_meter_provider = MeterProvider(metric_readers=[_prometheus_reader])
set_meter_provider(_meter_provider)
meter = get_meter_provider().get_meter("lecture_builder")


def install_auto_tracing() -> None:
    """Install Logfire auto-tracing restricted to repository modules."""

    def _in_project(module: logfire.AutoTraceModule) -> bool:
        filename = module.filename
        return filename is not None and Path(filename).resolve().is_relative_to(SRC_DIR)

    logfire.install_auto_tracing(
        modules=_in_project,
        min_duration=0,
        check_imported_modules="warn",
    )


def init_observability() -> None:
    """Configure Logfire and instrument global libraries.

    Reads configuration from environment variables so that instrumentation
    occurs before the application's settings module is imported. Behaviour is
    gated by the ``ENABLE_TRACING`` environment variable.
    """
    if os.getenv("ENABLE_TRACING", "").lower() not in {"1", "true", "yes", "on"}:
        return

    token = os.getenv("LOGFIRE_API_KEY")
    project = os.getenv("LOGFIRE_PROJECT")

    install_auto_tracing()
    logfire.configure(token=token, service_name=project)

    # Ensure loguru and the standard logging module send records to Logfire.
    # Clearing existing handlers prevents duplicate log entries.
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(logfire.LogfireLoggingHandler())

    loguru_logger.remove()
    loguru_logger.add(logfire.loguru_handler())

    logfire.instrument_pydantic()
    logfire.instrument_httpx()
    logfire.instrument_sqlalchemy()
    logfire.instrument_sqlite3()
    logfire.instrument_system_metrics()


def instrument_app(app: "FastAPI") -> None:
    """Instrument a FastAPI application and its ASGI server."""
    logfire.instrument_fastapi(app, capture_headers=True)
    logfire.instrument_asgi(cast(ASGIApp, app))  # type: ignore[arg-type]
