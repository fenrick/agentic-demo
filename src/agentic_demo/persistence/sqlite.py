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
            id TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS citations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT NOT NULL,
            citation TEXT NOT NULL,
            FOREIGN KEY(document_id) REFERENCES documents(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
