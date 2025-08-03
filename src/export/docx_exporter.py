"""Utilities for exporting stored workspace data to Microsoft Word (.docx)."""

from __future__ import annotations

import io
import json
import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from docx import Document as DocumentFactory
from docx.document import Document


@dataclass(slots=True)
class Outline:
    """Simple hierarchical outline used for DOCX export."""

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


class DocxExporter:
    """Render persisted lecture structures into a Word document."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def export(self, workspace_id: str) -> bytes:
        """Return a DOCX document for ``workspace_id`` as bytes."""

        with sqlite3.connect(self._db_path) as conn:
            outline = self._load_outline(conn, workspace_id)
            metadata = self._load_metadata(conn, workspace_id)
            citations = self._load_citations(conn, workspace_id)

        doc = DocumentFactory()
        self.generate_cover_page(doc, metadata)
        self.add_table_of_contents(doc)
        self.populate_sections(doc, outline)
        self.append_bibliography(doc, citations)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

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
    def generate_cover_page(doc: Document, metadata: Dict[str, str]) -> None:
        """Insert a simple title page based on ``metadata``."""

        doc.add_heading(metadata.get("topic", ""), level=0)
        doc.add_paragraph(f"Model: {metadata.get('model', '')}")
        doc.add_paragraph(f"Date: {metadata.get('date', '')}")

    @staticmethod
    def add_table_of_contents(doc: Document) -> None:
        """Insert a placeholder table of contents."""

        doc.add_heading("Table of Contents", level=1)
        doc.add_paragraph("TOC")

    @staticmethod
    def populate_sections(doc: Document, outline: Outline) -> None:
        """Populate ``doc`` with headings and bullet lists from ``outline``."""

        def walk(node: Outline, level: int) -> None:
            doc.add_heading(node.title, level=level)
            if node.objectives:
                doc.add_heading("Objectives", level=level + 1)
                for obj in node.objectives:
                    doc.add_paragraph(obj, style="List Bullet")
            if node.activities:
                doc.add_heading("Activities", level=level + 1)
                for act in node.activities:
                    doc.add_paragraph(act, style="List Bullet")
            if node.notes:
                doc.add_heading("Notes", level=level + 1)
                for note in node.notes:
                    doc.add_paragraph(note, style="List Bullet")
            for child in node.children:
                walk(child, level + 1)

        walk(outline, 2)

    @staticmethod
    def append_bibliography(doc: Document, citations: List[Citation]) -> None:
        """Append a bibliography section for ``citations``."""

        if not citations:
            return
        doc.add_heading("Bibliography", level=1)
        for cite in citations:
            entry = f"{cite.title} - {cite.url} (retrieved {cite.retrieved_at})"
            if cite.licence:
                entry += f" — {cite.licence}"
            doc.add_paragraph(entry, style="List Number")
