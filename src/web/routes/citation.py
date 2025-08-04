"""Citation related routes."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/citation")


@router.get("/{workspace_id}")
async def list_citations(workspace_id: str) -> list[dict[str, str]]:
    """Return stored citations for ``workspace_id``.

    The implementation is a placeholder that returns an empty list.
    """

    return []
