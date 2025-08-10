"""FastAPI endpoint exposing OpenTelemetry metrics in Prometheus format."""

from __future__ import annotations

from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


def get_metrics() -> Response:
    """Return metrics for Prometheus scrapers."""

    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
