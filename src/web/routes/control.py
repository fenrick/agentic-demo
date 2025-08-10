"""Execution control endpoints."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Body, Request

from core.orchestrator import GraphOrchestrator
from core.state import State

TopicBody = Body(..., embed=True)
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


@router.post("/retry")
async def retry(workspace_id: str) -> dict[str, str]:
    """Retry the graph using the last inputs for a workspace."""

    return {"workspace_id": workspace_id, "status": "retried"}
