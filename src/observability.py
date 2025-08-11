"""Logfire configuration and instrumentation helpers."""

from __future__ import annotations

import inspect
import logging
import os
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

import logfire
from loguru import logger as loguru_logger
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.metrics import get_meter_provider, set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from starlette.types import ASGIApp

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from fastapi import FastAPI


_prometheus_reader = PrometheusMetricReader()
_meter_provider = MeterProvider(metric_readers=[_prometheus_reader])
set_meter_provider(_meter_provider)
meter = get_meter_provider().get_meter("lecture_builder")

F = TypeVar("F", bound=Callable[..., Any])


def trace(fn: F) -> F:
    """Wrap ``fn`` execution in a ``logfire`` span named after the function."""

    if inspect.iscoroutinefunction(fn):

        @wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with logfire.span(fn.__name__):
                return await fn(*args, **kwargs)

        return cast(F, async_wrapper)

    @wraps(fn)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        with logfire.span(fn.__name__):
            return fn(*args, **kwargs)

    return cast(F, sync_wrapper)


@trace
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

    logfire.configure(token=token, service_name=project)
    logging.getLogger().addHandler(logfire.LogfireLoggingHandler())
    logfire.instrument_pydantic()
    logfire.instrument_httpx()
    logfire.instrument_sqlalchemy()
    logfire.instrument_sqlite3()
    logfire.instrument_system_metrics()
    loguru_logger.add(logfire.loguru_handler())


@trace
def instrument_app(app: "FastAPI") -> None:
    """Instrument a FastAPI application and its ASGI server."""
    logfire.instrument_fastapi(app, capture_headers=True)
    logfire.instrument_asgi(cast(ASGIApp, app))  # type: ignore[arg-type]
