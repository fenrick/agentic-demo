import sys
import types
from dataclasses import dataclass, field

import pytest
from core.state import State

# Stub modules to avoid heavy dependencies during import of core.policies
critics_stub = types.ModuleType("agents.critics")
critics_stub.CritiqueReport = type("CritiqueReport", (), {})  # type: ignore[attr-defined]
critics_stub.FactCheckReport = type("FactCheckReport", (), {})  # type: ignore[attr-defined]
sys.modules.setdefault("agents", types.ModuleType("agents"))
sys.modules["agents.critics"] = critics_stub


@dataclass(slots=True)
class DummyPlanResult:
    confidence: float


planner_stub = types.ModuleType("agents.planner")
planner_stub.PlanResult = DummyPlanResult  # type: ignore[attr-defined]
sys.modules["agents.planner"] = planner_stub

from core.policies import (  # noqa: E402
    policy_retry_on_critic_failure,
    policy_retry_on_low_confidence,
)


@dataclass(slots=True)
class DummyReport:
    issues: list[str] = field(default_factory=list)


def test_policy_retry_on_low_confidence_retries_until_limit():
    state = State(prompt="topic")
    result = DummyPlanResult(confidence=0.5)

    for _ in range(3):
        assert policy_retry_on_low_confidence(result, state) == "loop"
    assert state.retries["Planner"] == 3

    # Fourth attempt exceeds retry limit and returns "continue"
    assert policy_retry_on_low_confidence(result, state) == "continue"


def test_policy_retry_on_critic_failure_raises_after_limit():
    state = State(prompt="topic")
    report = DummyReport(issues=["bad"])

    for _ in range(3):
        assert policy_retry_on_critic_failure(report, state) is True
    assert state.retries["Content-Weaver"] == 3

    with pytest.raises(RuntimeError):
        policy_retry_on_critic_failure(report, state)
