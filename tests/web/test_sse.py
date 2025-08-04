import json

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from web.routes import register_sse_routes


@pytest.mark.asyncio
async def test_sse_uses_app_graph() -> None:
    events = [
        {"type": "state", "payload": {"n": 1}},
        {"type": "state", "payload": {"n": 2}},
        {"type": "state", "payload": {"n": 3}},
    ]
    called = {"flag": False}

    async def fake_astream(*args, **kwargs):
        called["flag"] = True
        for ev in events:
            yield ev

    app = FastAPI()
    app.state.graph = type("G", (), {"astream": fake_astream})()
    register_sse_routes(app)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream("GET", "/stream/foo/state") as response:
            payloads: list[dict[str, int]] = []
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:])
                    payloads.append(data["payload"])
                if len(payloads) == 3:
                    break

    assert called["flag"] is True
    assert payloads == [{"n": 1}, {"n": 2}, {"n": 3}]
