"""Utilities for exporting stored workspace data to Markdown."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(slots=True)
class Outline:
    """Simple hierarchical outline used for Markdown export."""

    title: str
    objectives: List[str] = field(default_factory=list)
    activities: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    children: List["Outline"] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict) -> "Outline":
        children = [cls.from_dict(child) for child in data.get("children", [])]
        return cls(
            title=data.get("title", ""),
            objectives=list(data.get("objectives", [])),
            activities=list(data.get("activities", [])),
            notes=list(data.get("notes", [])),
            children=children,
        )


@dataclass(slots=True)
class Citation:
    """Reference to an external information source."""

    url: str
    title: str
    retrieved_at: str
    licence: Optional[str] = None


class MarkdownExporter:
    """Render persisted lecture structures into Markdown."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def export(self, workspace_id: str) -> str:
        """Return a full Markdown document for ``workspace_id``."""

        with sqlite3.connect(self._db_path) as conn:
            outline = self._load_outline(conn, workspace_id)
            metadata = self._load_metadata(conn, workspace_id)
            citations = self._load_citations(conn, workspace_id)

        front = self.build_front_matter(metadata)
        body = self.render_outline(outline)
        cites = self.embed_citations(citations)
        return front + body + cites

    @staticmethod
    def _load_outline(conn: sqlite3.Connection, workspace_id: str) -> Outline:
        cur = conn.execute(
            "SELECT outline_json FROM outlines WHERE workspace_id = ? ORDER BY created_at DESC LIMIT 1",
            (workspace_id,),
        )
        row = cur.fetchone()
        cur.close()
        if row is None:
            raise ValueError("outline not found")
        return Outline.from_dict(json.loads(row[0]))

    @staticmethod
    def _load_metadata(conn: sqlite3.Connection, workspace_id: str) -> Dict[str, str]:
        cur = conn.execute(
            "SELECT topic, model, commit_sha, created_at FROM metadata WHERE workspace_id = ? ORDER BY created_at DESC LIMIT 1",
            (workspace_id,),
        )
        row = cur.fetchone()
        cur.close()
        if row is None:
            raise ValueError("metadata not found")
        return {"topic": row[0], "model": row[1], "commit": row[2], "date": row[3]}

    @staticmethod
    def _load_citations(conn: sqlite3.Connection, workspace_id: str) -> List[Citation]:
        cur = conn.execute(
            "SELECT url, title, retrieved_at, licence FROM citations WHERE workspace_id = ? ORDER BY rowid",
            (workspace_id,),
        )
        rows = cur.fetchall()
        cur.close()
        return [
            Citation(url=r[0], title=r[1], retrieved_at=r[2], licence=r[3])
            for r in rows
        ]

    @staticmethod
    def build_front_matter(metadata: Dict[str, str]) -> str:
        """Generate YAML front matter recognised by downstream tools."""

        lines = ["---"]
        for key in ("topic", "model", "commit", "date"):
            value = metadata.get(key, "")
            lines.append(f"{key}: {value}")
        lines.append("---\n")
        return "\n".join(lines)

    @staticmethod
    def render_outline(outline: Outline) -> str:
        """Render ``outline`` into Markdown headings and bullet lists."""

        lines: List[str] = []

        def walk(node: Outline, level: int) -> None:
            heading = "#" * level
            lines.append(f"{heading} {node.title}")
            if node.objectives:
                lines.append(f"{'#' * (level + 1)} Objectives")
                lines.extend(f"- {obj}" for obj in node.objectives)
            if node.activities:
                lines.append(f"{'#' * (level + 1)} Activities")
                lines.extend(f"- {act}" for act in node.activities)
            if node.notes:
                lines.append(f"{'#' * (level + 1)} Notes")
                lines.extend(f"- {note}" for note in node.notes)
            for child in node.children:
                walk(child, level + 1)

        walk(outline, 2)
        return "\n".join(lines) + "\n"

    @staticmethod
    def embed_citations(citations: List[Citation]) -> str:
        """Render footnote markers and a bibliography section."""

        if not citations:
            return ""
        markers = " ".join(f"[^{i}]" for i in range(1, len(citations) + 1))
        lines = [markers, "", "## Bibliography"]
        for i, cite in enumerate(citations, start=1):
            entry = f"[^{i}]: {cite.title} - {cite.url} (retrieved {cite.retrieved_at})"
            if cite.licence:
                entry += f" — {cite.licence}"
            lines.append(entry)
        return "\n".join(lines) + "\n"
