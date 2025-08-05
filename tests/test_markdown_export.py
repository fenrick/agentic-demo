from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agents.models import Activity, AssessmentItem, Citation, SlideBullet, WeaveResult
from export.markdown import embed_citations, from_weave_result, render_section
from export.markdown_exporter import MarkdownExporter


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
        summary="summary",
        slide_bullets=[SlideBullet(slide_number=1, bullets=["point"])],
        assessment=[AssessmentItem(type="quiz", description="q", max_score=1.0)],
    )
    citation = Citation(url="http://x", title="X", retrieved_at="2024-01-01")
    md = from_weave_result(weave, [citation])
    assert "title: Demo" in md
    assert "## Learning Objectives" in md
    assert "Slide 1" in md
    assert "Assessment" in md
    assert md.endswith("X - http://x (retrieved 2024-01-01)\n")
