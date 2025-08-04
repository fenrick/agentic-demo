"""Repository for managing retrieval cache entries."""

from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

import aiosqlite


class RetrievalCacheRepo:
    """Persist and retrieve cached search results."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def get(self, query: str) -> Optional[List[dict]]:
        """Return cached results for ``query`` if present.

        Increments the ``hit_count`` when a cache entry is found.
        """

        cur = await self._conn.execute(
            "SELECT results FROM retrieval_cache WHERE query = ?",
            (query,),
        )
        row = await cur.fetchone()
        await cur.close()
        if row is None:
            return None
        await self._conn.execute(
            "UPDATE retrieval_cache SET hit_count = hit_count + 1 WHERE query = ?",
            (query,),
        )
        await self._conn.commit()
        return json.loads(row[0])

    async def set(self, query: str, results: List[dict]) -> None:
        """Store ``results`` for ``query`` in the cache."""

        now = datetime.utcnow().isoformat()
        await self._conn.execute(
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
        await self._conn.commit()
