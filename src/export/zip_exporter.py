"""Package multiple export formats into a ZIP archive."""

from __future__ import annotations

import io
import zipfile
from typing import Dict

from .docx_exporter import DocxExporter
from .markdown_exporter import MarkdownExporter
from .metadata_exporter import export_citations_json
from .pdf_exporter import PdfExporter


class ZipExporter:
    """Generate a ZIP file containing multiple export formats."""

    def __init__(self, db_path: str, css_path: str | None = None) -> None:
        self._db_path = db_path
        self._css_path = css_path

    def collect_export_files(self, workspace_id: str) -> Dict[str, bytes]:
        """Collect individual export files for ``workspace_id``."""
        files: Dict[str, bytes] = {}
        md = MarkdownExporter(self._db_path).export(workspace_id)
        files["lecture.md"] = md.encode("utf-8")
        files["lecture.docx"] = DocxExporter(self._db_path).export(workspace_id)
        files["lecture.pdf"] = PdfExporter(self._db_path, self._css_path).export(
            workspace_id
        )
        files["citations.json"] = export_citations_json(self._db_path, workspace_id)
        return files

    @staticmethod
    def generate_zip(files: Dict[str, bytes]) -> bytes:
        """Bundle ``files`` into a ZIP archive and return the bytes."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for name, data in files.items():
                zf.writestr(name, data)
        return buf.getvalue()
