"""In-memory metrics collector that persists to SQLite."""

from __future__ import annotations

from datetime import datetime
from typing import List

from .models import MetricRecord
from .repository import MetricsRepository


class MetricsCollector:
    """Buffers metrics and flushes them to persistent storage."""

    def __init__(self, repository: MetricsRepository) -> None:
        self._repo = repository
        self._buffer: List[MetricRecord] = []

    def record(self, workspace_id: str, metric_name: str, value: float) -> None:
        """Append ``metric_name`` with ``value`` for ``workspace_id`` to the buffer."""

        record = MetricRecord(
            workspace_id=workspace_id,
            name=metric_name,
            value=value,
            timestamp=datetime.utcnow(),
        )
        self._buffer.append(record)

    def flush_to_db(self) -> None:
        """Persist buffered metrics to SQLite via the repository."""

        for record in self._buffer:
            self._repo.save(record)
        self._buffer.clear()
