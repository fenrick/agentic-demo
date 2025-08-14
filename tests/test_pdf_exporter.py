"""Tests for PDF export utilities."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

from export.pdf_exporter import PdfExporter


def test_render_pdf_requires_weasyprint(monkeypatch: pytest.MonkeyPatch) -> None:
    """It raises a helpful error when WeasyPrint is unavailable."""

    monkeypatch.delitem(sys.modules, "weasyprint", raising=False)
    exporter = PdfExporter(":memory:")
    with pytest.raises(RuntimeError) as excinfo:
        exporter.render_pdf("<html><head></head><body></body></html>")
    assert "WeasyPrint" in str(excinfo.value)


def test_pdf_exporter_includes_markdown_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """export produces HTML containing slide bullets and speaker notes."""

    db_path = tmp_path / "lecture.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE lectures (workspace_id TEXT, lecture_json TEXT, created_at TEXT)"
    )
    lecture = {
        "title": "Demo",
        "learning_objectives": ["lo"],
        "activities": [{"type": "Lecture", "description": "desc", "duration_min": 5}],
        "duration_min": 5,
        "slide_bullets": [{"slide_number": 1, "bullets": ["point"]}],
        "speaker_notes": "notes",
    }
    conn.execute(
        "INSERT INTO lectures VALUES (?,?,datetime('now'))",
        ("ws", json.dumps(lecture)),
    )
    conn.commit()
    conn.close()

    captured: dict[str, str] = {}

    def fake_render(html: str) -> bytes:
        captured["html"] = html
        return b"%PDF"

    monkeypatch.setattr(PdfExporter, "render_pdf", staticmethod(fake_render))

    exporter = PdfExporter(str(db_path))
    pdf_bytes = exporter.export("ws")
    assert pdf_bytes == b"%PDF"
    html = captured["html"]
    assert "Slide 1" in html
    assert "Speaker Notes" in html
