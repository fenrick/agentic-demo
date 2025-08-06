"""Helpers for exporting lecture data into multiple formats."""

from __future__ import annotations

from .markdown_exporter import MarkdownExporter
from .metadata_exporter import export_citations_json
from .pdf_exporter import PdfExporter

__all__ = [
    "MarkdownExporter",
    "PdfExporter",
    "export_citations_json",
    "EXPORTERS",
]


EXPORTERS = {
    "markdown": MarkdownExporter,
    "pdf": PdfExporter,
    "metadata": export_citations_json,
}
