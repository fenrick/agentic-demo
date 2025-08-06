"""Integration-style tests for retry control flow."""

import sys
import types
from dataclasses import dataclass, field
from itertools import cycle

import pytest
from core.state import Outline, State

# Stub modules so core.policies can be imported without heavy dependencies
critics_stub = types.ModuleType("agents.critics")


@dataclass(slots=True)
class DummyCritiqueReport:
    """Minimal critique report with recommendations."""

    recommendations: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DummyFactCheckReport:
    """Minimal fact-check report with issue counters."""

    hallucination_count: int = 0
    unsupported_claims_count: int = 0


critics_stub.CritiqueReport = DummyCritiqueReport  # type: ignore[attr-defined]
critics_stub.FactCheckReport = DummyFactCheckReport  # type: ignore[attr-defined]

planner_stub = types.ModuleType("agents.planner")


@dataclass(slots=True)
class DummyPlanResult:
    """Planner result with a confidence score."""

    confidence: float


planner_stub.PlanResult = DummyPlanResult  # type: ignore[attr-defined]

sys.modules.setdefault("agents", types.ModuleType("agents"))
sys.modules["agents.critics"] = critics_stub
sys.modules["agents.planner"] = planner_stub

from core.policies import (  # noqa: E402
    policy_retry_on_critic_failure,
    policy_retry_on_low_confidence,
)


@pytest.mark.asyncio
async def test_planner_loops_researcher_until_retry_limit() -> None:
    """Planner loops through researcher until retry ceiling is hit."""

    calls = {"researcher": 0}

    async def fake_planner(state: State) -> DummyPlanResult:
        state.outline = Outline(steps=["draft"])
        return DummyPlanResult(confidence=0.1)

    async def fake_researcher(_state: State) -> None:
        calls["researcher"] += 1

    state = State(prompt="topic")
    while True:
        result = await fake_planner(state)
        decision = policy_retry_on_low_confidence(result, state)
        if decision == "continue":
            break
        await fake_researcher(state)

    assert calls["researcher"] == 3
    assert state.retries["Planner"] == 3
    assert state.outline.steps == ["draft"]


@pytest.mark.asyncio
async def test_content_weaver_reinvoked_until_retry_ceiling() -> None:
    """Critic failures reinvoke content weaver up to the retry limit."""

    calls = {"weaver": 0}

    async def fake_weaver(_state: State) -> None:
        calls["weaver"] += 1

    state = State(prompt="topic", outline=Outline(steps=["draft"]))
    reports = cycle(
        [
            DummyCritiqueReport(recommendations=["revise"]),
            DummyFactCheckReport(hallucination_count=1),
        ]
    )

    with pytest.raises(RuntimeError):
        while True:
            await fake_weaver(state)
            report = next(reports)
            if policy_retry_on_critic_failure(report, state):
                continue
            break

    assert calls["weaver"] == 4
    assert state.retries["Content-Weaver"] == 3
    assert state.outline.steps == ["draft"]
