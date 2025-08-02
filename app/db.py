"""SQLite helper utilities for the demo application."""

from __future__ import annotations

import sqlite3
from pathlib import Path

# TODO(#test_foreign_key_enforced): add support for cascading deletes when removing runs.

DDL = """
CREATE TABLE runs      (id INTEGER PRIMARY KEY, topic TEXT, started_at DATETIME, finished_at DATETIME);
CREATE TABLE versions  (id INTEGER PRIMARY KEY, run_id INTEGER, step INTEGER, body_markdown TEXT, created_at DATETIME,
                        FOREIGN KEY(run_id) REFERENCES runs(id));
CREATE TABLE citations (id INTEGER PRIMARY KEY, version_id INTEGER, url TEXT, snippet TEXT,
                        FOREIGN KEY(version_id) REFERENCES versions(id));
CREATE TABLE logs      (id INTEGER PRIMARY KEY, run_id INTEGER, agent TEXT, thought TEXT, result TEXT, created_at DATETIME,
                        FOREIGN KEY(run_id) REFERENCES runs(id));
"""

_CONN: sqlite3.Connection | None = None


def connect(path: str = "agentic.db") -> sqlite3.Connection:
    """Return a SQLite connection with WAL enabled.

    Parameters
    ----------
    path:
        Filesystem path to the database file.
    """

    global _CONN
    if _CONN is not None:
        return _CONN
    first = not Path(path).exists()
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    if first:
        conn.executescript(DDL)
        conn.commit()
    _CONN = conn
    return conn


def get_cursor() -> sqlite3.Cursor:
    """Return a cursor for the active connection."""

    if _CONN is None:
        connect()
    assert _CONN is not None
    return _CONN.cursor()


def commit() -> None:
    """Commit the current transaction."""

    if _CONN is None:
        raise RuntimeError("Database not initialised")
    _CONN.commit()
