from datetime import datetime
from pathlib import Path

from metrics.alerts import AlertManager
from metrics.models import MetricRecord
from metrics.repository import MetricsRepository


def _insert(
    repo: MetricsRepository, ws: str, ped: float, hall: float, cost: float
) -> None:
    now = datetime.utcnow()
    repo.save(
        MetricRecord(
            workspace_id=ws, name="pedagogical_score", value=ped, timestamp=now
        )
    )
    repo.save(
        MetricRecord(
            workspace_id=ws, name="hallucination_rate", value=hall, timestamp=now
        )
    )
    repo.save(MetricRecord(workspace_id=ws, name="cost", value=cost, timestamp=now))


def test_evaluate_thresholds_flags_breaches(tmp_path: Path) -> None:
    repo = MetricsRepository(str(tmp_path / "metrics.db"))
    _insert(repo, "ws1", 0.8, 0.03, 0.7)
    manager = AlertManager(repo, thresholds_path=Path("src/config/thresholds.yaml"))
    summary = manager.evaluate_thresholds("ws1")
    assert summary.pedagogical_breached
    assert summary.hallucination_breached
    assert summary.cost_breached


def test_evaluate_thresholds_no_breaches(tmp_path: Path) -> None:
    repo = MetricsRepository(str(tmp_path / "metrics.db"))
    _insert(repo, "ws1", 0.95, 0.01, 0.5)
    manager = AlertManager(repo, thresholds_path=Path("src/config/thresholds.yaml"))
    summary = manager.evaluate_thresholds("ws1")
    assert not summary.has_breaches
