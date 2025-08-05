"""Tests for :mod:`export.metadata_exporter`."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from export.metadata_exporter import export_citations_json


def _setup_db(path: Path) -> Path:
    db_path = path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE citations (workspace_id TEXT, url TEXT, title TEXT, retrieved_at"
        " TEXT, licence TEXT)"
    )
    conn.execute(
        "INSERT INTO citations VALUES (?,?,?,?,?)",
        ("ws1", "http://example.com", "Example", "2024-01-01", None),
    )
    conn.commit()
    conn.close()
    return db_path


def test_export_citations_json_structure(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    data = export_citations_json(str(db), "ws1")
    cites = json.loads(data.decode("utf-8"))
    assert cites == [
        {
            "url": "http://example.com",
            "title": "Example",
            "retrieved_at": "2024-01-01",
            "licence": None,
        }
    ]
