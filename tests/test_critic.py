import pytest

from agentic_demo.orchestration import critic
from agentic_demo.orchestration.state import State
import agentic_demo.orchestration.graph as graph


@pytest.mark.asyncio
async def test_critic_retries_until_success(monkeypatch):
    calls = {"count": 0}

    async def failing_eval(state: State) -> float:
        calls["count"] += 1
        if calls["count"] < 3:
            raise RuntimeError("boom")
        return 0.8

    monkeypatch.setattr(graph, "_evaluate", failing_eval)
    state = State()
    result = await critic(state)
    assert result["critic_score"] == 0.8
    assert state.critic_attempts == 1
    assert state.log == ["critic"]
    assert calls["count"] == 3


@pytest.mark.asyncio
async def test_critic_raises_after_max_retries(monkeypatch):
    async def always_fail(state: State) -> float:
        raise RuntimeError("boom")

    monkeypatch.setattr(graph, "_evaluate", always_fail)
    state = State()
    with pytest.raises(RuntimeError):
        await critic(state)
    assert state.log == []
    assert state.critic_attempts == 0
