import json

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import web.sse as sse_module
from web.routes import register_sse_routes


@pytest.mark.asyncio
async def test_sse_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_astream(*args, **kwargs):
        events = [
            {"type": "start", "payload": {}},
            {"type": "update", "payload": {}},
            {"type": "end", "payload": {}},
        ]
        for ev in events:
            yield ev

    monkeypatch.setattr(sse_module, "graph", type("G", (), {"astream": fake_astream})())

    app = FastAPI()
    register_sse_routes(app)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream("GET", "/stream/foo") as response:
            types: list[str] = []
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:])
                    types.append(data["type"])
                if len(types) == 3:
                    break

    assert types == ["start", "update", "end"]
