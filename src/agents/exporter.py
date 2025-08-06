"""Exporter node triggering document renders."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass

from config import settings
from core.state import ActionLog, State
from export.docx_exporter import DocxExporter
from export.markdown_exporter import MarkdownExporter
from export.pdf_exporter import PdfExporter


@dataclass(slots=True)
class ExportStatus:
    """Status of export operations."""

    success: bool = True


async def run_exporter(state: State) -> ExportStatus:
    """Trigger Markdown/DOCX/PDF renders and report completion.

    Parameters
    ----------
    state:
        Mutable orchestration state. A ``workspace_id`` attribute is expected to
        be present on the instance identifying which workspace should be
        exported. The function mutates ``state`` by appending log entries and by
        recording the filesystem locations of the generated files under an
        ``exports`` attribute.

    Returns
    -------
    ExportStatus
        Simple dataclass indicating whether all export operations succeeded.

    Notes
    -----
    Expected I/O and database errors are captured and recorded in ``state.log``.
    Unexpected exceptions are logged and re-raised so callers can handle them.
    """

    workspace_id = getattr(state, "workspace_id", "default")

    db_path = settings.data_dir / "workspace.db"
    export_dir = settings.data_dir / "exports" / workspace_id
    export_dir.mkdir(parents=True, exist_ok=True)

    status = ExportStatus(success=True)
    exported: dict[str, str] = {}

    try:
        md = MarkdownExporter(str(db_path)).export(workspace_id)
        md_path = export_dir / "lecture.md"
        md_path.write_text(md, encoding="utf-8")
        exported["markdown"] = str(md_path)

        docx_bytes = DocxExporter(str(db_path)).export(workspace_id)
        docx_path = export_dir / "lecture.docx"
        docx_path.write_bytes(docx_bytes)
        exported["docx"] = str(docx_path)

        pdf_bytes = PdfExporter(str(db_path)).export(workspace_id)
        pdf_path = export_dir / "lecture.pdf"
        pdf_path.write_bytes(pdf_bytes)
        exported["pdf"] = str(pdf_path)

        state.log.append(ActionLog(message="Export complete"))
        state.exports = exported
    except (OSError, sqlite3.Error, ValueError) as exc:
        logging.exception("Export failed")
        state.log.append(ActionLog(message=f"Export failed: {exc}"))
        status.success = False
    except Exception as exc:  # pragma: no cover - unexpected
        logging.exception("Unexpected export failure")
        state.log.append(ActionLog(message=f"Export failed: {exc}"))
        raise

    return status
