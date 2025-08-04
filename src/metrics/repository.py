"""SQLite repository for persisting metrics."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List

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
            "INSERT INTO metrics (name, value, timestamp) VALUES (?, ?, ?)",
            (metric.name, metric.value, metric.timestamp.isoformat()),
        )
        self._conn.commit()

    def query(self, time_range: TimeRange) -> List[MetricRecord]:
        """Return metrics within ``time_range``."""

        cur = self._conn.execute(
            """
            SELECT name, value, timestamp FROM metrics
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp
            """,
            (time_range.start.isoformat(), time_range.end.isoformat()),
        )
        rows = cur.fetchall()
        return [
            MetricRecord(
                name=row["name"],
                value=row["value"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
            )
            for row in rows
        ]
