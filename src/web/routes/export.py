"""Export-related routes."""

from __future__ import annotations

from fastapi import APIRouter, Response

from web.api.export_endpoints import (
    get_markdown_export,
    get_docx_export,
    get_pdf_export,
    get_citations_json,
    get_all_exports,
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
