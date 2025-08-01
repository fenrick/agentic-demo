import asyncio
from unittest.mock import patch

import pytest

from app.agents import ChatAgent, plan, research, draft, review


@pytest.mark.asyncio
async def test_plan_async():
    with patch.object(ChatAgent, "__call__", return_value="p"):
        result = await asyncio.to_thread(plan, "topic")
    assert result == "p"


@pytest.mark.asyncio
async def test_research_async():
    with (
        patch.object(ChatAgent, "__call__", return_value="r"),
        patch("app.agents.perplexity.search", return_value="notes"),
    ):
        result = await asyncio.to_thread(research, "outline")
    assert result == "r"


@pytest.mark.asyncio
async def test_draft_async():
    with patch.object(ChatAgent, "__call__", return_value="d"):
        result = await asyncio.to_thread(draft, "notes")
    assert result == "d"


@pytest.mark.asyncio
async def test_review_async():
    with patch.object(ChatAgent, "__call__", return_value="v"):
        result = await asyncio.to_thread(review, "text")
    assert result == "v"
