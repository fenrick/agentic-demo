"""Tests for the SQLite persistence layer."""

import sqlite3
from pathlib import Path

import pytest

from agentic_demo.persistence import AsyncSqliteSaver


@pytest.mark.asyncio
async def test_init_creates_tables(tmp_path: Path) -> None:
    """Initializing the saver applies schema migrations."""
    db_path = tmp_path / "test.db"
    saver = AsyncSqliteSaver(db_path)
    await saver.init()
    conn = sqlite3.connect(db_path)
    try:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()
    assert {"state", "documents", "citations", "logs"} <= tables
