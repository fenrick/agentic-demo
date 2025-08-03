"""Tests for :mod:`export.docx_exporter`."""

from __future__ import annotations

import json
import sqlite3
from io import BytesIO
from pathlib import Path

from docx import Document

from export.docx_exporter import DocxExporter


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


def _doc_from_bytes(data: bytes) -> Document:
    return Document(BytesIO(data))


def test_export_returns_valid_docx_bytes(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    exporter = DocxExporter(str(db))
    data = exporter.export("ws1")
    assert data[:2] == b"PK"
    # Ensure document can be parsed
    _doc_from_bytes(data)


def test_cover_page_contents_present(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    data = DocxExporter(str(db)).export("ws1")
    doc = _doc_from_bytes(data)
    texts = [p.text for p in doc.paragraphs]
    assert any("AI" in t for t in texts)
    assert any("2024-01-01" in t for t in texts)


def test_toc_is_inserted(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    data = DocxExporter(str(db)).export("ws1")
    doc = _doc_from_bytes(data)
    texts = [p.text for p in doc.paragraphs]
    assert any("Table of Contents" in t for t in texts)


def test_bibliography_section_populated(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    data = DocxExporter(str(db)).export("ws1")
    doc = _doc_from_bytes(data)
    texts = [p.text for p in doc.paragraphs]
    assert any("Bibliography" in t for t in texts)
    assert any(
        "Example - http://example.com (retrieved 2024-01-01)" in t for t in texts
    )
