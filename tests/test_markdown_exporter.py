"""Tests for :mod:`export.markdown_exporter`."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from export.markdown_exporter import MarkdownExporter


def _setup_db(path: Path) -> Path:
    db_path = path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE outlines (workspace_id TEXT, outline_json TEXT, created_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE metadata (workspace_id TEXT, topic TEXT, model TEXT, commit_sha TEXT, created_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE citations (workspace_id TEXT, url TEXT, title TEXT, retrieved_at TEXT, licence TEXT)"
    )
    outline = {
        "title": "Intro to AI",
        "objectives": ["Understand basics"],
        "activities": ["Lecture"],
        "notes": ["Remember"],
        "children": [
            {
                "title": "History",
                "objectives": ["History objective"],
                "activities": [],
                "notes": [],
            }
        ],
    }
    conn.execute(
        "INSERT INTO outlines VALUES (?,?,?)",
        ("ws1", json.dumps(outline), "2024-01-01"),
    )
    conn.execute(
        "INSERT INTO metadata VALUES (?,?,?,?,?)",
        ("ws1", "AI", "gpt-4", "abc123", "2024-01-01"),
    )
    conn.execute(
        "INSERT INTO citations VALUES (?,?,?,?,?)",
        ("ws1", "http://example.com", "Example", "2024-01-01", None),
    )
    conn.commit()
    conn.close()
    return db_path


def test_export_generates_markdown_structure(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    exporter = MarkdownExporter(str(db))
    md = exporter.export("ws1")
    assert md.startswith("---")
    assert "## Intro to AI" in md
    assert "### History" in md
    assert "### Objectives" in md


def test_front_matter_contains_required_fields(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    md = MarkdownExporter(str(db)).export("ws1")
    assert "topic: AI" in md
    assert "model: gpt-4" in md
    assert "commit: abc123" in md
    assert "date: 2024-01-01" in md


def test_citation_footnotes_and_bibliography_presence(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    md = MarkdownExporter(str(db)).export("ws1")
    assert "[^1]" in md
    assert "## Bibliography" in md
    assert "[^1]: Example - http://example.com (retrieved 2024-01-01)" in md
