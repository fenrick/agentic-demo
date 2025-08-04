"""Tests for the exporter agent node."""

from __future__ import annotations

import importlib
import json
import sqlite3
from pathlib import Path

import pytest


def _setup_db(path: Path) -> None:
    """Create a minimal workspace database under ``path``."""

    db_path = path / "workspace.db"
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


@pytest.mark.asyncio
async def test_run_exporter_writes_all_formats(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Exporter writes Markdown, DOCX and PDF outputs to disk."""

    monkeypatch.setenv("OPENAI_API_KEY", "sk")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "pk")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    import config

    importlib.reload(config)

    _setup_db(tmp_path)

    import agents.exporter as exporter

    importlib.reload(exporter)

    from core.state import State

    state = State(prompt="hi")
    state.workspace_id = "ws1"

    status = await exporter.run_exporter(state)
    assert status.success

    export_dir = tmp_path / "exports" / "ws1"
    assert (export_dir / "lecture.md").exists()
    assert (export_dir / "lecture.docx").exists()
    assert (export_dir / "lecture.pdf").exists()
    assert "markdown" in getattr(state, "exports")
