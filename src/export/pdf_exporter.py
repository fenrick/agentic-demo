"""Utilities for exporting stored workspace data to PDF."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import markdown
from weasyprint import HTML

from .markdown_exporter import MarkdownExporter


class PdfExporter:
    """Render a persisted workspace to a styled PDF document."""

    def __init__(self, db_path: str, css_path: Optional[str] | None = None) -> None:
        """Create a new exporter.

        Args:
            db_path: Location of the SQLite database.
            css_path: Optional path to a CSS file for PDF styling.
        """

        self._db_path = db_path
        self._css_path = css_path

    def export(self, workspace_id: str) -> bytes:
        """Return a PDF document for ``workspace_id`` as bytes."""

        md = MarkdownExporter(self._db_path).export(workspace_id)
        html = self.convert_markdown_to_html(md)
        styled = self.apply_css(html)
        return self.render_pdf(styled)

    @staticmethod
    def convert_markdown_to_html(md: str) -> str:
        """Convert Markdown text to minimal HTML."""

        body = markdown.markdown(md, extensions=["footnotes"])
        return f"<html><head></head><body>{body}</body></html>"

    def apply_css(self, html: str) -> str:
        """Embed CSS into the HTML document if ``css_path`` was provided."""

        if not self._css_path:
            return html
        try:
            css = Path(self._css_path).read_text(encoding="utf-8")
        except OSError:
            return html
        return html.replace("</head>", f"<style>{css}</style></head>", 1)

    @staticmethod
    def render_pdf(html: str) -> bytes:
        """Render HTML content into PDF bytes using WeasyPrint."""

        return HTML(string=html).write_pdf()
