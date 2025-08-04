"""SQLite repository for persisting metrics."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import MetricRecord, TimeRange


class MetricsRepository:
    """CRUD operations for the ``metrics`` table."""

    def __init__(self, db_path: str | Path) -> None:
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._ensure_table()

    def _ensure_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                workspace_id TEXT NOT NULL,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def save(self, metric: MetricRecord) -> None:
        """Insert ``metric`` into the database."""

        self._conn.execute(
            "INSERT INTO metrics (workspace_id, name, value, timestamp) VALUES (?, ?, ?, ?)",
            (
                metric.workspace_id,
                metric.name,
                metric.value,
                metric.timestamp.isoformat(),
            ),
        )
        self._conn.commit()

    def query(
        self, time_range: TimeRange, workspace_id: Optional[str] = None
    ) -> List[MetricRecord]:
        """Return metrics within ``time_range``.

        Parameters
        ----------
        time_range:
            Range to search within.
        workspace_id:
            If provided, restrict results to this workspace.
        """

        if workspace_id is None:
            cur = self._conn.execute(
                """
                SELECT workspace_id, name, value, timestamp FROM metrics
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
                """,
                (time_range.start.isoformat(), time_range.end.isoformat()),
            )
        else:
            cur = self._conn.execute(
                """
                SELECT workspace_id, name, value, timestamp FROM metrics
                WHERE workspace_id = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp
                """,
                (
                    workspace_id,
                    time_range.start.isoformat(),
                    time_range.end.isoformat(),
                ),
            )
        rows = cur.fetchall()
        return [
            MetricRecord(
                workspace_id=row["workspace_id"],
                name=row["name"],
                value=row["value"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
            )
            for row in rows
        ]

    def latest_value(self, workspace_id: str, metric_name: str) -> Optional[float]:
        """Return the most recent value for ``metric_name`` in ``workspace_id``."""

        cur = self._conn.execute(
            """
            SELECT value FROM metrics
            WHERE workspace_id = ? AND name = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (workspace_id, metric_name),
        )
        row = cur.fetchone()
        return float(row["value"]) if row else None
