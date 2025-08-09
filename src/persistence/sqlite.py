"""SQLite-based persistence utilities."""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path


class AsyncSqliteSaver:
    """Persist workspace data asynchronously to a SQLite database.

    Parameters
    ----------
    path:
        Filesystem location of the SQLite database.
    """

    _MIGRATIONS: tuple[str, ...] = (
        """
        CREATE TABLE IF NOT EXISTS state (
            id INTEGER PRIMARY KEY,
            payload_json TEXT NOT NULL,
            version INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_id INTEGER NOT NULL,
            parquet_blob BLOB NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(state_id) REFERENCES state(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS citations (
            workspace_id TEXT NOT NULL,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            licence TEXT NOT NULL,
            PRIMARY KEY (workspace_id, url)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS retrieval_cache (
            query TEXT PRIMARY KEY,
            results TEXT NOT NULL,
            hit_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workspace_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            input_hash TEXT NOT NULL,
            output_hash TEXT NOT NULL,
            tokens INTEGER NOT NULL,
            cost REAL NOT NULL,
            timestamp TEXT NOT NULL
        );
        """,
    )

    path: Path

    def __init__(self, path: Path) -> None:
        self.path = path

    async def init(self) -> None:
        """Initialize the database and apply migrations.

        Side Effects
        ------------
        Creates the database file and applies initial schema.

        Raises
        ------
        sqlite3.Error
            If applying migrations fails.
        """

        await asyncio.to_thread(self._apply_migrations)

    def _apply_migrations(self) -> None:
        """Apply schema migrations synchronously."""
        conn = sqlite3.connect(self.path)
        try:
            cur = conn.cursor()
            for statement in self._MIGRATIONS:
                cur.executescript(statement)
            conn.commit()
        finally:
            conn.close()
