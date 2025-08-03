"""Repository for document blobs tied to state versions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

import aiosqlite


@dataclass
class DocumentMetadata:
    """Metadata about a stored document blob."""

    id: int
    created_at: datetime


class DocumentRepo:
    """Manage the ``documents`` table."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def save_document_version(self, state_id: int, blob: bytes) -> int:
        """Persist ``blob`` for ``state_id`` and return new row id."""
        now = datetime.utcnow().isoformat()
        cur = await self._conn.execute(
            """
            INSERT INTO documents (state_id, parquet_blob, created_at)
            VALUES (?, ?, ?)
            """,
            (state_id, blob, now),
        )
        await self._conn.commit()
        return cur.lastrowid

    async def list_versions(self, state_id: int) -> List[DocumentMetadata]:
        """Return all document versions for ``state_id``."""
        cur = await self._conn.execute(
            "SELECT id, created_at FROM documents WHERE state_id = ? ORDER BY created_at",
            (state_id,),
        )
        rows = await cur.fetchall()
        await cur.close()
        return [
            DocumentMetadata(id=row[0], created_at=datetime.fromisoformat(row[1]))
            for row in rows
        ]

    async def load_latest_document(self, state_id: int) -> bytes:
        """Return the most recent document blob for ``state_id``."""
        cur = await self._conn.execute(
            """
            SELECT parquet_blob FROM documents
            WHERE state_id = ? ORDER BY created_at DESC LIMIT 1
            """,
            (state_id,),
        )
        row = await cur.fetchone()
        await cur.close()
        if row is None:
            raise ValueError(f"no documents for state_id {state_id}")
        return row[0]
