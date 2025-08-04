"""FastAPI endpoint that evaluates metric thresholds and sends alerts."""

from __future__ import annotations

from fastapi import Request, Response, status

from metrics.alerts import AlertManager
from metrics.repository import MetricsRepository


def post_alerts(workspace_id: str, request: Request) -> Response:
    """Evaluate metrics for ``workspace_id`` and trigger webhook if breached."""

    db_path: str = request.app.state.db_path
    repo = MetricsRepository(db_path)
    manager = AlertManager(repo)
    summary = manager.evaluate_thresholds(workspace_id)
    if summary.has_breaches:
        manager.send_webhook(summary)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
