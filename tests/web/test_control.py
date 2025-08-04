import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from web.routes.control import router as control_router


@pytest.mark.asyncio
async def test_run_and_resume_endpoints() -> None:
    app = FastAPI()
    app.include_router(control_router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        run_resp = await client.post("/run", json={"topic": "math"})
        assert run_resp.status_code == 201
        job_id = run_resp.json()["job_id"]
        assert isinstance(job_id, str) and job_id

        resume_resp = await client.post(f"/resume/{job_id}")
        assert resume_resp.status_code == 200
        assert resume_resp.json() == {"job_id": job_id, "status": "resumed"}
