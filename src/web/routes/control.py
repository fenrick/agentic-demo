"""Execution control endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Body

router = APIRouter(prefix="/control")


@router.post("/{workspace_id}/run")
async def run_workspace(workspace_id: str) -> dict[str, str]:
    """Start processing for a workspace.

    This is a stub implementation used for testing the HTTP interface.
    """

    return {"workspace": workspace_id, "status": "running"}


@router.post("/{workspace_id}/pause")
async def pause_workspace(workspace_id: str) -> dict[str, str]:
    """Pause processing for a workspace."""

    return {"workspace": workspace_id, "status": "paused"}


@router.post("/{workspace_id}/model")
async def select_model(
    workspace_id: str, model: str = Body(..., embed=True)
) -> dict[str, str]:
    """Select the active model for a workspace."""

    return {"workspace": workspace_id, "model": model}
