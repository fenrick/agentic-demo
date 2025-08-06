"""Citation related routes."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/workspaces/{workspace_id}/citations")


@router.get("")
async def list_citations(workspace_id: str) -> list[dict[str, str]]:
    """Return stored citations for ``workspace_id``.

    The implementation is a placeholder that returns an empty list.
    """

    return []


@router.get("/{citation_id}")
async def get_citation(workspace_id: str, citation_id: str) -> dict[str, str]:
    """Return citation ``citation_id`` for ``workspace_id``.

    The implementation is a placeholder that returns minimal metadata.
    """

    return {
        "url": f"https://example.org/{citation_id}",
        "title": "Placeholder",
        "retrieved_at": "1970-01-01",
        "licence": "unknown",
    }
