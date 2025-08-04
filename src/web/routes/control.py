"""Execution control endpoints."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Body

router = APIRouter()


@router.post("/run", status_code=201)
async def run(topic: str = Body(..., embed=True)) -> dict[str, str]:
    """Start a new lecture generation job.

    This endpoint is a stub used for testing the HTTP interface.
    """

    return {"job_id": str(uuid4())}


@router.post("/resume/{job_id}")
async def resume(job_id: str) -> dict[str, str]:
    """Resume processing for a previously started job."""

    return {"job_id": job_id, "status": "resumed"}
