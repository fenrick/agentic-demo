from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

import pytest

from agents.exporter import run_exporter
from agents.models import Activity, AssessmentItem, Citation, SlideBullet, WeaveResult
from config import settings
from core.state import State
from export.markdown import embed_citations, from_weave_result, render_section
from export.markdown_exporter import MarkdownExporter

os.environ.setdefault("OPENAI_API_KEY", "test")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def test_render_section_handles_strings_and_iterables() -> None:
    """render_section outputs headings with strings or bullet lists."""

    assert render_section("Title", "text").startswith("## Title\ntext")
    assert render_section("Title", ["a", "b"]).strip() == "## Title\n- a\n- b"
    assert render_section("Title", None) == ""


def test_embed_citations_appends_footnotes() -> None:
    """embed_citations adds sequential footnotes to Markdown text."""

    base = "content"
    cites = [Citation(url="http://x", title="X", retrieved_at="2024-01-01")]
    md = embed_citations(base, cites)
    assert md.endswith("X - http://x (retrieved 2024-01-01)\n")
    assert "[^1]" in md


def test_markdown_exporter_reads_from_database(tmp_path: Path) -> None:
    """MarkdownExporter.export loads lecture data and renders Markdown."""

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
        "references": [{"url": "http://x", "title": "X", "retrieved_at": "2024-01-01"}],
    }
    conn.execute(
        "INSERT INTO lectures VALUES (?,?,datetime('now'))",
        ("ws", json.dumps(lecture)),
    )
    conn.commit()
    conn.close()

    exporter = MarkdownExporter(str(db_path))
    md = exporter.export("ws")
    assert "title: Demo" in md
    assert "duration_min: 5" in md
    assert "## Duration" in md
    assert "5 min" in md
    assert "Slide 1" in md
    assert "Speaker Notes" in md
    assert "[^1]" in md


def test_from_weave_result_builds_complete_document() -> None:
    """from_weave_result assembles all sections of the document."""

    weave = WeaveResult(
        title="Demo",
        learning_objectives=["understand"],
        activities=[Activity(type="Lecture", description="desc", duration_min=10)],
        duration_min=10,
        author="Author",
        date="2024-01-01",
        version="1.0",
        summary="summary",
        tags=["t1"],
        prerequisites=["p"],
        slide_bullets=[SlideBullet(slide_number=1, bullets=["point"])],
        speaker_notes="notes",
        assessment=[AssessmentItem(type="quiz", description="q", max_score=1.0)],
    )
    citation = Citation(url="http://x", title="X", retrieved_at="2024-01-01")
    md = from_weave_result(weave, [citation])
    assert "title: Demo" in md
    assert "duration_min: 10" in md
    assert "## Duration" in md
    assert "10 min" in md
    assert "tags: [t1]" in md
    assert "## Learning Objectives" in md
    assert "## Prerequisites" in md
    assert "Speaker Notes" in md
    assert "Slide 1" in md
    assert "Assessment" in md
    assert md.endswith("X - http://x (retrieved 2024-01-01)\n")


@pytest.mark.asyncio
async def test_run_exporter_handles_expected_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """run_exporter reports failure for anticipated exceptions."""

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    state = State(prompt="p")
    state.workspace_id = "ws"
    status = await run_exporter(state)
    assert not status.success
    assert any("Export failed" in entry.message for entry in state.log)


@pytest.mark.asyncio
async def test_run_exporter_reraises_unexpected_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """run_exporter bubbles up unanticipated exceptions."""

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    state = State(prompt="p")
    state.workspace_id = "ws"

    def boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(MarkdownExporter, "export", boom)
    with pytest.raises(RuntimeError):
        await run_exporter(state)
    assert any("Export failed" in entry.message for entry in state.log)
