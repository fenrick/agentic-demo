import logging

import pytest

from core.orchestrator import GraphOrchestrator, Node
from core.state import State


@pytest.mark.asyncio
async def test_stream_logs_pithy_messages(caplog):
    async def noop(_state: State) -> None:
        return None

    flow = [
        Node("Learning-Advisor", noop, "Editor"),
        Node("Editor", noop, None),
    ]
    orch = GraphOrchestrator(flow)
    state = State(prompt="Photosynthesis")
    with caplog.at_level(logging.INFO):
        async for _ in orch.stream(state):
            pass
    assert "Crafting lesson plans for Photosynthesis" in caplog.text
    assert "Reviewing narrative for Photosynthesis" in caplog.text
