"""Tests for :mod:`export.pdf_exporter`."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from export.markdown_exporter import MarkdownExporter
from export.pdf_exporter import PdfExporter


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


def test_html_generation_from_markdown(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    md = MarkdownExporter(str(db)).export("ws1")
    html = PdfExporter(str(db)).convert_markdown_to_html(md)
    assert "<h2>Intro to AI</h2>" in html


def test_css_injection(tmp_path: Path) -> None:
    css_file = tmp_path / "style.css"
    css_file.write_text("body { color: red; }")
    exporter = PdfExporter("", str(css_file))
    styled = exporter.apply_css("<html><head></head><body>hi</body></html>")
    assert "body { color: red; }" in styled


def test_pdf_bytes_are_non_empty(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    exporter = PdfExporter(str(db))
    data = exporter.export("ws1")
    assert data[:4] == b"%PDF"
    assert len(data) > 0
