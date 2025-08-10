import pytest
from httpx import AsyncClient

from web.main import create_app


@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_counters() -> None:
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:  # type: ignore[call-arg]
        await client.get("/healthz")
        resp = await client.get("/api/metrics")
    assert resp.status_code == 200
    assert "requests_total" in resp.text
