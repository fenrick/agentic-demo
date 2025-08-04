import asyncio
import sys
import types

fake_config = types.SimpleNamespace(
    settings=types.SimpleNamespace(model_name="gpt-test")
)
sys.modules.setdefault("agentic_demo", types.SimpleNamespace(config=fake_config))

from agents import planner  # noqa: E402
from core.state import State  # noqa: E402


def test_run_planner_parses_outline_and_confidence(monkeypatch):
    async def fake_llm(prompt: str) -> str:
        return "1. Intro\n2. Body\n3. Conclusion"

    monkeypatch.setattr(planner, "call_planner_llm", fake_llm)

    async def run_test():
        state = State(prompt="topic")
        return await planner.run_planner(state)

    result = asyncio.run(run_test())
    assert result.outline.steps == ["Intro", "Body", "Conclusion"]
    assert result.confidence == 0.8


def test_run_planner_empty_response(monkeypatch):
    async def fake_llm(prompt: str) -> str:
        return ""

    monkeypatch.setattr(planner, "call_planner_llm", fake_llm)

    async def run_test():
        state = State(prompt="topic")
        return await planner.run_planner(state)

    result = asyncio.run(run_test())
    assert result.outline.steps == []
    assert result.confidence == 0.0
