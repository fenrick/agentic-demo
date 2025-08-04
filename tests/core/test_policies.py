"""Unit tests for policy and retry helpers."""

from __future__ import annotations

import os
import sys
import types
from dataclasses import dataclass

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("PERPLEXITY_API_KEY", "test")
os.environ.setdefault("DATA_DIR", "/tmp")

import pytest


@dataclass
class PlanResult:
    """Minimal planner result used for testing."""

    confidence: float


@dataclass
class CritiqueReport:
    """Minimal critique report for testing."""

    issues: list[str] | None = None


class FactCheckReport(CritiqueReport):
    """Alias for :class:`CritiqueReport` used by critic policy."""


@dataclass
class CitationResult:
    """Simplified citation result for merge tests."""

    url: str
    content: str


critics_mod = types.ModuleType("agents.critics")
critics_mod.CritiqueReport = CritiqueReport
critics_mod.FactCheckReport = FactCheckReport
sys.modules["agents.critics"] = critics_mod

planner_mod = types.ModuleType("agents.planner")
planner_mod.PlanResult = PlanResult
sys.modules["agents.planner"] = planner_mod

research_mod = types.ModuleType("web.researcher_web")
research_mod.CitationResult = CitationResult
sys.modules["web.researcher_web"] = research_mod

from core.policies import (  # noqa: E402
    merge_research_results,
    policy_retry_on_critic_failure,
    policy_retry_on_low_confidence,
    retry_tracker,
)
from core.state import State  # noqa: E402


def test_policy_retry_on_low_confidence() -> None:
    """Planner with low confidence should trigger a retry."""

    state = State()
    assert policy_retry_on_low_confidence(PlanResult(confidence=0.5), state)
    assert not policy_retry_on_low_confidence(PlanResult(confidence=0.9), state)


def test_policy_retry_on_low_confidence_limit() -> None:
    """A fourth planner retry should raise an error."""

    state = State()
    result = PlanResult(confidence=0.1)
    for _ in range(3):
        assert policy_retry_on_low_confidence(result, state)
    with pytest.raises(RuntimeError):
        policy_retry_on_low_confidence(result, state)


def test_policy_retry_on_critic_failure() -> None:
    """Presence of issues should trigger a content rewrite."""

    state = State()
    assert policy_retry_on_critic_failure(CritiqueReport(issues=["gap"]), state)
    assert not policy_retry_on_critic_failure(CritiqueReport(), state)


def test_policy_retry_on_critic_failure_limit() -> None:
    """A fourth rewrite should raise an error."""

    state = State()
    report = CritiqueReport(issues=["gap"])
    for _ in range(3):
        assert policy_retry_on_critic_failure(report, state)
    with pytest.raises(RuntimeError):
        policy_retry_on_critic_failure(report, state)


def test_merge_research_results_dedupes_urls() -> None:
    """Duplicate URLs should be collapsed while preserving order."""

    results = [
        CitationResult(url="https://a.com", content="1"),
        CitationResult(url="https://a.com/", content="2"),
        CitationResult(url="https://b.com", content="3"),
    ]
    merged = merge_research_results(results)
    assert [c.url for c in merged] == ["https://a.com", "https://b.com"]


def test_retry_tracker_enforces_limit() -> None:
    """Tracker should raise after exceeding three retries."""

    state = State()
    for i in range(3):
        assert retry_tracker(state, "node") == i + 1
    with pytest.raises(RuntimeError):
        retry_tracker(state, "node")
