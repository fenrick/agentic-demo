import logging

import pytest

from core.orchestrator import GraphOrchestrator, Node
from core.state import State


@pytest.mark.asyncio
async def test_stream_logs_pithy_messages(caplog):
    async def noop(_state: State) -> None:
        return None

    flow = [
        Node("Content-Weaver", noop, "Pedagogy-Critic"),
        Node("Pedagogy-Critic", noop, None),
    ]
    orch = GraphOrchestrator(flow)
    state = State(prompt="Photosynthesis")
    with caplog.at_level(logging.INFO):
        async for _ in orch.stream(state):
            pass
    assert "Weaving content from different sources for Photosynthesis" in caplog.text
    assert "Assessing learning outcomes for Photosynthesis" in caplog.text
