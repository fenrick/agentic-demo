"""Export citation metadata to JSON."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List


def export_citations_json(db_path: str, workspace_id: str) -> bytes:
    """Serialize citation records for ``workspace_id`` to JSON bytes."""
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT url, title, retrieved_at, licence FROM citations WHERE workspace_id = ? ORDER BY rowid",
            (workspace_id,),
        )
        rows = cur.fetchall()
        cur.close()
    citations: List[Dict[str, Any]] = []
    for url, title, retrieved_at, licence in rows:
        citations.append(
            {
                "url": url,
                "title": title,
                "retrieved_at": retrieved_at,
                "licence": licence,
            }
        )
    return json.dumps(citations).encode("utf-8")
