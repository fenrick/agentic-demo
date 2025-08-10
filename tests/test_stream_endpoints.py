"""Tests for SSE streaming endpoints."""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from agents.streaming import stream, stream_messages
from web.main import app


@pytest.mark.asyncio
async def test_stream_messages_endpoint() -> None:
    """Messages endpoint forwards streamed tokens."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream("GET", "/stream/messages") as response:
            await asyncio.sleep(0)
            stream_messages("hello")
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    assert "hello" in line
                    break


@pytest.mark.asyncio
async def test_stream_workspace_messages_endpoint() -> None:
    """Workspace messages endpoint forwards streamed tokens."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        workspace_id = "abc123"
        async with client.stream("GET", f"/stream/{workspace_id}/messages") as response:
            await asyncio.sleep(0)
            stream(f"{workspace_id}:messages", "world")
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    assert "world" in line
                    break
