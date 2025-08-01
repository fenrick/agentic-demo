import json
import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from app.graph import build_graph
from app.overlay_agent import OverlayAgent
from app.agents import ChatAgent

DATA_PATH = Path(__file__).with_name("golden_graph.json")


@pytest.mark.asyncio
async def test_graph_golden(tmp_path):
    expected = json.loads(DATA_PATH.read_text())
    with (
        patch("app.graph.plan", return_value="plan"),
        patch("app.graph.research", return_value="research"),
        patch("app.graph.draft", return_value="draft"),
        patch("app.graph.review", return_value="review"),
        patch("app.agents.ChatAgent.__call__", return_value="overlay"),
        patch("app.graph.OverlayAgent") as Agent,
    ):
        Agent.return_value = OverlayAgent(ChatAgent())
        flow = build_graph(mode="overlay")
        result = await asyncio.to_thread(flow.run, "topic")
    assert result == expected
