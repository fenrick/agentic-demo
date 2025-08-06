"""Export-related routes."""

from __future__ import annotations

from fastapi import APIRouter, Response

from web.api.export_endpoints import (
    ExportStatus,
    ExportUrls,
    get_all_exports,
    get_citations_json,
    get_docx_export,
    get_export_status,
    get_export_urls,
    get_markdown_export,
    get_pdf_export,
)

router = APIRouter()

router.add_api_route(
    "/export/{workspace_id}/md",
    get_markdown_export,
    methods=["GET"],
    response_class=Response,
)
router.add_api_route(
    "/export/{workspace_id}/docx",
    get_docx_export,
    methods=["GET"],
    response_class=Response,
)
router.add_api_route(
    "/export/{workspace_id}/pdf",
    get_pdf_export,
    methods=["GET"],
    response_class=Response,
)
router.add_api_route(
    "/export/{workspace_id}/citations.json",
    get_citations_json,
    methods=["GET"],
    response_class=Response,
)
router.add_api_route(
    "/export/{workspace_id}/all",
    get_all_exports,
    methods=["GET"],
    response_class=Response,
)

router.add_api_route(
    "/workspaces/{workspace_id}/export/status",
    get_export_status,
    methods=["GET"],
    response_model=ExportStatus,
)

router.add_api_route(
    "/workspaces/{workspace_id}/export/urls",
    get_export_urls,
    methods=["GET"],
    response_model=ExportUrls,
)
