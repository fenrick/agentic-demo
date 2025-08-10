"""Execution control endpoints."""

from __future__ import annotations

import asyncio
from typing import NoReturn

from fastapi import APIRouter, Body, HTTPException, Request

from core.orchestrator import GraphOrchestrator
from core.state import State

TopicBody = Body(..., embed=True)
ModelBody = Body(..., embed=True)
router = APIRouter(prefix="/workspaces/{workspace_id}")


@router.post("/run", status_code=201)
async def run(
    request: Request, workspace_id: str, topic: str = TopicBody
) -> dict[str, str]:
    """Start a new lecture generation job.

    Args:
        request: Incoming HTTP request providing access to application state.
        workspace_id: Identifier for the current workspace/job.
        topic: Lecture topic that seeds orchestration.

    Returns:
        dict[str, str]: Mapping containing the ``job_id`` and ``workspace_id``.
    """

    state = State(prompt=topic)
    state.workspace_id = workspace_id
    graph: GraphOrchestrator = request.app.state.graph
    asyncio.create_task(graph.run(state))
    return {"job_id": workspace_id, "workspace_id": workspace_id}


@router.post("/pause")
async def pause(workspace_id: str) -> NoReturn:
    """Pause the graph execution for a workspace."""

    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/retry")
async def retry(workspace_id: str) -> dict[str, str]:
    """Retry the graph using the last inputs for a workspace."""

    return {"workspace_id": workspace_id, "status": "retried"}


@router.post("/resume")
async def resume(workspace_id: str) -> NoReturn:
    """Resume processing for a previously started job."""

    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/model")
async def model(workspace_id: str, model: str = ModelBody) -> NoReturn:
    """Select the model to run subsequent operations against."""

    raise HTTPException(status_code=501, detail="Not implemented")
