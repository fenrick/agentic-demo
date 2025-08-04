"""FastAPI endpoint exposing recent metrics in Prometheus format."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import Request, Response

from metrics.models import TimeRange
from metrics.repository import MetricsRepository


def get_metrics(request: Request) -> Response:
    """Return recent metrics formatted for Prometheus scrapers."""

    db_path: str = request.app.state.db_path
    repo = MetricsRepository(db_path)
    end = datetime.utcnow()
    start = end - timedelta(minutes=5)
    records = repo.query(TimeRange(start=start, end=end))
    body = "\n".join(f"{m.name} {m.value}" for m in records)
    return Response(content=body, media_type="text/plain")
