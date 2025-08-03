import pytest

from agentic_demo.orchestration import critic
import agentic_demo.orchestration.graph as graph
from core.state import State


def test_critic_retries_until_success(monkeypatch):
    calls = {"count": 0}

    def failing_eval(state: State) -> float:
        calls["count"] += 1
        if calls["count"] < 3:
            raise RuntimeError("boom")
        return 0.8

    monkeypatch.setattr(graph, "_evaluate", failing_eval)
    state = State()
    result = critic(state)
    assert result["log"] == [{"message": "critic"}]
    assert [entry.message for entry in state.log] == ["critic"]
    assert calls["count"] == 3


def test_critic_raises_after_max_retries(monkeypatch):
    def always_fail(state: State) -> float:
        raise RuntimeError("boom")

    monkeypatch.setattr(graph, "_evaluate", always_fail)
    state = State()
    with pytest.raises(RuntimeError):
        critic(state)
    assert state.log == []
