from datetime import datetime, timedelta
from pathlib import Path

from metrics.collector import MetricsCollector
from metrics.repository import MetricsRepository
from metrics.models import TimeRange


def test_record_and_flush_persists_metrics(tmp_path: Path) -> None:
    db = tmp_path / "metrics.db"
    repo = MetricsRepository(str(db))
    collector = MetricsCollector(repo)

    collector.record("ws1", "tokens", 5.0)
    # Nothing should be persisted before flush
    now = datetime.utcnow()
    recent = repo.query(
        TimeRange(start=now - timedelta(minutes=1), end=now + timedelta(minutes=1)),
        workspace_id="ws1",
    )
    assert recent == []

    collector.flush_to_db()

    end = datetime.utcnow() + timedelta(minutes=1)
    start = end - timedelta(minutes=2)
    rows = repo.query(TimeRange(start=start, end=end), workspace_id="ws1")
    assert len(rows) == 1
    assert rows[0].name == "tokens"
    assert rows[0].value == 5.0
