from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from metrics.models import MetricRecord
from metrics.repository import MetricsRepository
from web.metrics_endpoint import get_metrics


def _setup_db(path: Path) -> Path:
    db = path / "metrics.db"
    repo = MetricsRepository(str(db))
    now = datetime.utcnow()
    repo.save(MetricRecord(name="tokens", value=10.0, timestamp=now))
    repo.save(MetricRecord(name="cost", value=0.5, timestamp=now))
    return db


def test_get_metrics_returns_prometheus_text(tmp_path: Path) -> None:
    db_path = _setup_db(tmp_path)
    app = FastAPI()
    app.state.db_path = str(db_path)
    app.add_api_route("/metrics", get_metrics, methods=["GET"])
    client = TestClient(app)

    res = client.get("/metrics")
    assert res.status_code == 200
    body = res.text.splitlines()
    assert "tokens 10.0" in body
    assert "cost 0.5" in body
