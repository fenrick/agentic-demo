"""Unit tests for policy decision helpers."""

import sys
import types
from dataclasses import dataclass, field

import pytest

from core.policies import (  # noqa: E402
    policy_retry_on_critic_failure,
    policy_retry_on_low_confidence,
)
from core.state import State

# Stub modules to avoid heavy dependencies during import of core.policies
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
sys.modules.setdefault("agents", types.ModuleType("agents"))
sys.modules["agents.critics"] = critics_stub


@dataclass(slots=True)
class DummyPlanResult:
    """Planner result with a confidence score."""

    confidence: float


planner_stub = types.ModuleType("agents.planner")
planner_stub.PlanResult = DummyPlanResult  # type: ignore[attr-defined]
sys.modules["agents.planner"] = planner_stub


def test_policy_retry_on_low_confidence_retries_until_limit() -> None:
    """Planner should loop until retry limit then continue."""

    state = State(prompt="topic")
    result = DummyPlanResult(confidence=0.5)

    for _ in range(3):
        assert policy_retry_on_low_confidence(result, state) == "loop"
    assert state.retries["Planner"] == 3

    # Fourth attempt exceeds retry limit and returns "continue"
    assert policy_retry_on_low_confidence(result, state) == "continue"


@pytest.mark.parametrize(
    "report",
    [
        DummyCritiqueReport(recommendations=["fix"]),
        DummyFactCheckReport(hallucination_count=1),
    ],
)
def test_policy_retry_on_critic_failure_stops_after_limit(report) -> None:
    """Critic failures trigger retries until the limit then continue."""

    state = State(prompt="topic")

    for _ in range(3):
        assert policy_retry_on_critic_failure(report, state) is True
    assert state.retries["Content-Weaver"] == 3

    # Fourth attempt exceeds retry limit and returns False instead of raising
    assert policy_retry_on_critic_failure(report, state) is False
