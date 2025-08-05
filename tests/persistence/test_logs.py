"""Tests for action log persistence."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from persistence import get_db_session
from persistence.logs import compute_hash, get_logs, log_action

CREATE_TABLE_SQL = """
CREATE TABLE action_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    tokens INTEGER NOT NULL,
    cost REAL NOT NULL,
    timestamp TEXT NOT NULL
)
"""


@pytest.mark.asyncio
async def test_log_action_persists(tmp_path, monkeypatch):
    """log_action stores a single record."""

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "x")
    monkeypatch.setenv("MODEL_NAME", "model")
    async with get_db_session() as conn:
        await conn.execute(CREATE_TABLE_SQL)
        await conn.commit()
        ts = datetime.utcnow()
        await log_action(
            conn,
            "ws1",
            "critic",
            "in_hash",
            "out_hash",
            10,
            0.1,
            ts,
        )
        cur = await conn.execute(
            "SELECT workspace_id, agent_name, input_hash, output_hash, tokens, cost,"
            " timestamp FROM action_logs"
        )
        rows = await cur.fetchall()
        assert rows == [
            ("ws1", "critic", "in_hash", "out_hash", 10, 0.1, ts.isoformat())
        ]


@pytest.mark.asyncio
async def test_get_logs_filters_by_workspace_and_date(tmp_path, monkeypatch):
    """get_logs returns logs within the requested date range for a workspace."""

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "x")
    monkeypatch.setenv("MODEL_NAME", "model")
    async with get_db_session() as conn:
        await conn.execute(CREATE_TABLE_SQL)
        await conn.commit()
        t1 = datetime(2023, 1, 1, 12, 0)
        t2 = datetime(2023, 1, 2, 12, 0)
        t3 = datetime(2023, 1, 3, 12, 0)
        await log_action(conn, "ws1", "a", "i1", "o1", 1, 0.0, t1)
        await log_action(conn, "ws1", "b", "i2", "o2", 2, 0.0, t2)
        await log_action(conn, "ws2", "c", "i3", "o3", 3, 0.0, t2)
        await log_action(conn, "ws1", "d", "i4", "o4", 4, 0.0, t3)
        logs = await get_logs(conn, "ws1", date(2023, 1, 2), date(2023, 1, 3))
        assert [log.agent_name for log in logs] == ["b", "d"]
        assert all(log.workspace_id == "ws1" for log in logs)


def test_compute_hash_deterministic():
    """compute_hash returns consistent hashes for identical payloads."""

    payload = {"a": 1, "b": 2}
    assert compute_hash(payload) == compute_hash(payload)
