"""Utilities for exporting stored lecture data to Markdown."""

from __future__ import annotations

import json
import sqlite3

from agents.models import (Activity, AssessmentItem, Citation, SlideBullet,
                           WeaveResult)

from .markdown import from_weave_result


class MarkdownExporter:
    """Render persisted lecture structures into Markdown."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def export(self, workspace_id: str) -> str:
        """Return a full Markdown document for ``workspace_id``."""

        with sqlite3.connect(self._db_path) as conn:
            lecture = self._load_lecture(conn, workspace_id)
        return from_weave_result(lecture, lecture.references or [])

    @staticmethod
    def _load_lecture(conn: sqlite3.Connection, workspace_id: str) -> WeaveResult:
        cur = conn.execute(
            "SELECT lecture_json FROM lectures WHERE workspace_id = ? ORDER BY created_at DESC LIMIT 1",
            (workspace_id,),
        )
        row = cur.fetchone()
        cur.close()
        if row is None:
            raise ValueError("lecture not found")
        data = json.loads(row[0])
        activities = [Activity(**a) for a in data.get("activities", [])]
        slide_bullets = [SlideBullet(**s) for s in data.get("slide_bullets", [])]
        assessment = [AssessmentItem(**a) for a in data.get("assessment", [])]
        references = [Citation(**c) for c in data.get("references", [])]
        return WeaveResult(
            title=data["title"],
            learning_objectives=data.get("learning_objectives", []),
            activities=activities,
            duration_min=data.get("duration_min", 0),
            author=data.get("author"),
            date=data.get("date"),
            version=data.get("version"),
            summary=data.get("summary"),
            tags=data.get("tags"),
            prerequisites=data.get("prerequisites"),
            slide_bullets=slide_bullets or None,
            speaker_notes=data.get("speaker_notes"),
            assessment=assessment or None,
            references=references or None,
        )
