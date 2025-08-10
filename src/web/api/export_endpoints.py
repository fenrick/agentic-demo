"""FastAPI routes for exporting workspace data."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

from export.docx_exporter import DocxExporter
from export.markdown_exporter import MarkdownExporter
from export.metadata_exporter import export_citations_json
from export.pdf_exporter import PdfExporter
from export.zip_exporter import ZipExporter
from web.telemetry import EXPORT_DURATION


class ExportStatus(BaseModel):
    """Readiness of generated export artifacts."""

    ready: bool


class ExportUrls(BaseModel):
    """Download links for available export formats."""

    md: str
    docx: str
    pdf: str
    zip: str


async def get_export_status(request: Request, workspace_id: str) -> ExportStatus:
    """Return whether all export files exist for ``workspace_id``."""

    data_dir: Path = request.app.state.settings.data_dir
    export_dir = data_dir / "exports" / workspace_id
    expected = ["lecture.md", "lecture.docx", "lecture.pdf"]
    ready = all((export_dir / name).exists() for name in expected)
    return ExportStatus(ready=ready)


async def get_export_urls(workspace_id: str) -> ExportUrls:
    """Produce download URLs for export files."""

    return ExportUrls(
        md=f"/export/{workspace_id}/md",
        docx=f"/export/{workspace_id}/docx",
        pdf=f"/export/{workspace_id}/pdf",
        zip=f"/export/{workspace_id}/all",
    )


async def get_markdown_export(request: Request, workspace_id: str) -> Response:
    """Return Markdown for ``workspace_id`` with appropriate headers."""
    db_path: str = request.app.state.db_path
    start = perf_counter()
    md = MarkdownExporter(db_path).export(workspace_id)
    EXPORT_DURATION.record((perf_counter() - start) * 1000, {"format": "md"})
    headers = {"Content-Disposition": "attachment; filename=lecture.md"}
    return Response(content=md, media_type="text/markdown", headers=headers)


async def get_docx_export(request: Request, workspace_id: str) -> Response:
    """Return a DOCX export for ``workspace_id``."""
    db_path: str = request.app.state.db_path
    start = perf_counter()
    docx_bytes = DocxExporter(db_path).export(workspace_id)
    EXPORT_DURATION.record((perf_counter() - start) * 1000, {"format": "docx"})
    headers = {"Content-Disposition": "attachment; filename=lecture.docx"}
    return Response(
        content=docx_bytes,
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        headers=headers,
    )


async def get_pdf_export(request: Request, workspace_id: str) -> Response:
    """Return a PDF export for ``workspace_id``."""
    db_path: str = request.app.state.db_path
    start = perf_counter()
    pdf_bytes = PdfExporter(db_path).export(workspace_id)
    EXPORT_DURATION.record((perf_counter() - start) * 1000, {"format": "pdf"})
    headers = {"Content-Disposition": "attachment; filename=lecture.pdf"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


async def get_citations_json(request: Request, workspace_id: str) -> Response:
    """Return citation metadata for ``workspace_id`` as JSON bytes."""
    db_path: str = request.app.state.db_path
    start = perf_counter()
    json_bytes = export_citations_json(db_path, workspace_id)
    EXPORT_DURATION.record((perf_counter() - start) * 1000, {"format": "citations"})
    headers = {"Content-Disposition": "attachment; filename=citations.json"}
    return Response(content=json_bytes, media_type="application/json", headers=headers)


async def get_all_exports(request: Request, workspace_id: str) -> Response:
    """Return all export formats bundled into a ZIP archive."""
    db_path: str = request.app.state.db_path
    start = perf_counter()
    files = ZipExporter(db_path).collect_export_files(workspace_id)
    zip_bytes = ZipExporter.generate_zip(files)
    EXPORT_DURATION.record((perf_counter() - start) * 1000, {"format": "zip"})
    headers = {"Content-Disposition": "attachment; filename=exports.zip"}
    return Response(content=zip_bytes, media_type="application/zip", headers=headers)


def register_export_routes(app: FastAPI) -> None:
    """Attach export endpoints to ``app``."""
    app.add_api_route(
        "/export/{workspace_id}/md",
        get_markdown_export,
        methods=["GET"],
        response_class=Response,
    )
    app.add_api_route(
        "/export/{workspace_id}/docx",
        get_docx_export,
        methods=["GET"],
        response_class=Response,
    )
    app.add_api_route(
        "/export/{workspace_id}/pdf",
        get_pdf_export,
        methods=["GET"],
        response_class=Response,
    )
    app.add_api_route(
        "/export/{workspace_id}/citations.json",
        get_citations_json,
        methods=["GET"],
        response_class=Response,
    )
    app.add_api_route(
        "/export/{workspace_id}/all",
        get_all_exports,
        methods=["GET"],
        response_class=Response,
    )
