"""Tests for database initialization via Alembic."""

import os
import sqlite3
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_init_db_creates_all_tables(tmp_path: Path) -> None:
    os.environ["OPENAI_API_KEY"] = "x"
    os.environ["PERPLEXITY_API_KEY"] = "y"
    os.environ["DATA_DIR"] = str(tmp_path)

    from config import Settings
    from persistence.database import init_db

    settings = Settings()
    db_path = await init_db(settings)
    conn = sqlite3.connect(db_path)
    try:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()
    assert {
        "state",
        "documents",
        "citations",
        "action_logs",
        "metrics",
        "critique_report",
        "factcheck_report",
    } <= tables
