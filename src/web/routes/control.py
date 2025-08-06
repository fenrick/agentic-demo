"""Execution control endpoints."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Body

router = APIRouter(prefix="/workspaces/{workspace_id}")


@router.post("/run", status_code=201)
async def run(workspace_id: str, topic: str = Body(..., embed=True)) -> dict[str, str]:
    """Start a new lecture generation job.

    This endpoint is a stub used for testing the HTTP interface.
    """

    return {"job_id": str(uuid4())}


@router.post("/pause")
async def pause(workspace_id: str) -> dict[str, str]:
    """Pause the graph execution for a workspace."""

    return {"workspace_id": workspace_id, "status": "paused"}


@router.post("/retry")
async def retry(workspace_id: str) -> dict[str, str]:
    """Retry the graph using the last inputs for a workspace."""

    return {"workspace_id": workspace_id, "status": "retried"}


@router.post("/resume")
async def resume(workspace_id: str) -> dict[str, str]:
    """Resume processing for a previously started job."""

    return {"workspace_id": workspace_id, "status": "resumed"}


@router.post("/model")
async def model(
    workspace_id: str, model: str = Body(..., embed=True)
) -> dict[str, str]:
    """Select the model to run subsequent operations against."""

    return {"workspace_id": workspace_id, "model": model}
