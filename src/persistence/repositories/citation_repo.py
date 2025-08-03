"""Repository for managing citations."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import aiosqlite

from ..models import Citation


class CitationRepo:
    """Provide CRUD operations for :class:`Citation` records."""

    def __init__(self, conn: aiosqlite.Connection, workspace_id: str) -> None:
        self._conn = conn
        self._workspace_id = workspace_id

    async def insert(self, citation: Citation) -> None:
        """Insert or replace a citation record."""

        await self._conn.execute(
            """
            INSERT OR REPLACE INTO citations (workspace_id, url, title, retrieved_at, licence)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                self._workspace_id,
                str(citation.url),
                citation.title,
                citation.retrieved_at.isoformat(),
                citation.licence,
            ),
        )
        await self._conn.commit()

    async def get_by_url(self, url: str) -> Optional[Citation]:
        """Return a citation matching ``url`` if present."""

        cur = await self._conn.execute(
            """
            SELECT url, title, retrieved_at, licence FROM citations
            WHERE workspace_id = ? AND url = ?
            """,
            (self._workspace_id, url),
        )
        row = await cur.fetchone()
        await cur.close()
        if row is None:
            return None
        return Citation(
            url=row[0],
            title=row[1],
            retrieved_at=datetime.fromisoformat(row[2]),
            licence=row[3],
        )

    async def list_by_workspace(self, workspace_id: str) -> List[Citation]:
        """List all citations for ``workspace_id``."""

        cur = await self._conn.execute(
            """
            SELECT url, title, retrieved_at, licence FROM citations
            WHERE workspace_id = ?
            """,
            (workspace_id,),
        )
        rows = await cur.fetchall()
        await cur.close()
        return [
            Citation(
                url=row[0],
                title=row[1],
                retrieved_at=datetime.fromisoformat(row[2]),
                licence=row[3],
            )
            for row in rows
        ]
