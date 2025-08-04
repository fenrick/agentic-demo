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
        "CREATE TABLE lectures (workspace_id TEXT, lecture_json TEXT, created_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE citations (workspace_id TEXT, url TEXT, title TEXT, retrieved_at TEXT, licence TEXT)"
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


def test_html_generation_from_markdown(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    md = MarkdownExporter(str(db)).export("ws1")
    html = PdfExporter(str(db)).convert_markdown_to_html(md)
    assert "<h2>Summary</h2>" in html


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
