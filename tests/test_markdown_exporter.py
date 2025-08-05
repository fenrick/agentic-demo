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
        "CREATE TABLE lectures (workspace_id TEXT, lecture_json TEXT, created_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE citations (workspace_id TEXT, url TEXT, title TEXT, retrieved_at"
        " TEXT, licence TEXT)"
    )
    lecture = {
        "title": "Intro to AI",
        "author": "Alice",
        "date": "2024-01-01",
        "version": "1.0",
        "summary": "Basics of AI",
        "tags": ["ai", "intro"],
        "prerequisites": ["Python"],
        "duration_min": 60,
        "learning_objectives": ["Understand basics"],
        "activities": [
            {
                "type": "Lecture",
                "description": "Overview",
                "duration_min": 30,
                "learning_objectives": ["Understand basics"],
            }
        ],
        "slide_bullets": [{"slide_number": 1, "bullets": ["What is AI?", "History"]}],
        "speaker_notes": "Engage audience",
        "assessment": [{"type": "Quiz", "description": "Check", "max_score": 10}],
        "references": [
            {
                "url": "http://example.com",
                "title": "Example",
                "retrieved_at": "2024-01-01",
                "licence": "CC",
            }
        ],
    }
    conn.execute(
        "INSERT INTO lectures VALUES (?,?,?)",
        ("ws1", json.dumps(lecture), "2024-01-01"),
    )
    conn.execute(
        "INSERT INTO citations VALUES (?,?,?,?,?)",
        ("ws1", "http://example.com", "Example", "2024-01-01", "CC"),
    )
    conn.commit()
    conn.close()
    return db_path


def test_export_generates_markdown_structure(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    exporter = MarkdownExporter(str(db))
    md = exporter.export("ws1")
    assert "## Summary" in md
    assert "## Learning Objectives" in md
    assert "## Prerequisites" in md
    assert "Slide 1" in md
    assert "## Assessment" in md
    assert "## References" in md


def test_front_matter_contains_required_fields(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    md = MarkdownExporter(str(db)).export("ws1")
    assert "title: Intro to AI" in md
    assert "author: Alice" in md
    assert "version: 1.0" in md
    assert "tags: [ai, intro]" in md


def test_citation_footnotes_and_bibliography_presence(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    md = MarkdownExporter(str(db)).export("ws1")
    assert "[^1]" in md
    assert "## References" in md
    assert "[^1]: Example - http://example.com (retrieved 2024-01-01) — CC" in md
