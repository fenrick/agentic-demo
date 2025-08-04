"""SQLite-backed action log utilities."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any, List

import aiosqlite

from models import ActionLog


def compute_hash(payload: Any) -> str:
    """Return a SHA-256 hash for ``payload``."""

    data = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


async def log_action(
    conn: aiosqlite.Connection,
    workspace_id: str,
    agent_name: str,
    input_hash: str,
    output_hash: str,
    tokens: int,
    cost: float,
    timestamp: datetime,
) -> None:
    """Persist a single agent invocation."""

    await conn.execute(
        """
        INSERT INTO action_logs (
            workspace_id,
            agent_name,
            input_hash,
            output_hash,
            tokens,
            cost,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            workspace_id,
            agent_name,
            input_hash,
            output_hash,
            tokens,
            cost,
            timestamp.isoformat(),
        ),
    )
    await conn.commit()


async def get_logs(
    conn: aiosqlite.Connection,
    workspace_id: str,
    date_from: date,
    date_to: date,
) -> List[ActionLog]:
    """Return logs for ``workspace_id`` within the date range."""

    cur = await conn.execute(
        """
        SELECT workspace_id, agent_name, input_hash, output_hash, tokens, cost, timestamp
        FROM action_logs
        WHERE workspace_id = ? AND date(timestamp) BETWEEN ? AND ?
        ORDER BY timestamp
        """,
        (workspace_id, date_from.isoformat(), date_to.isoformat()),
    )
    rows = await cur.fetchall()
    await cur.close()
    return [
        ActionLog(
            workspace_id=row[0],
            agent_name=row[1],
            input_hash=row[2],
            output_hash=row[3],
            tokens=row[4],
            cost=row[5],
            timestamp=datetime.fromisoformat(row[6]),
        )
        for row in rows
    ]
