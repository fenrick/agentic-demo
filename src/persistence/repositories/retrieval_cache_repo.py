"""Repository for managing retrieval cache entries."""

from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

import asyncio
import sqlite3


class RetrievalCacheRepo:
    """Persist and retrieve cached search results."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    async def get(self, query: str) -> Optional[List[dict]]:
        """Return cached results for ``query`` if present.

        Increments the ``hit_count`` when a cache entry is found.
        """

        cur = self._conn.execute(
            "SELECT results FROM retrieval_cache WHERE query = ?",
            (query,),
        )
        row = cur.fetchone()
        cur.close()
        if row is None:
            await asyncio.sleep(0)
            return None
        self._conn.execute(
            "UPDATE retrieval_cache SET hit_count = hit_count + 1 WHERE query = ?",
            (query,),
        )
        self._conn.commit()
        await asyncio.sleep(0)
        return json.loads(row[0])

    async def set(self, query: str, results: List[dict]) -> None:
        """Store ``results`` for ``query`` in the cache."""

        now = datetime.utcnow().isoformat()
        self._conn.execute(
            """
            INSERT OR REPLACE INTO retrieval_cache (query, results, hit_count, created_at)
            VALUES (
                ?,
                ?,
                COALESCE((SELECT hit_count FROM retrieval_cache WHERE query = ?), 0),
                ?
            )
            """,
            (query, json.dumps(results), query, now),
        )
        self._conn.commit()
        await asyncio.sleep(0)
