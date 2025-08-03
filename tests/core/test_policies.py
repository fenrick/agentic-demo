"""Unit tests for policy and retry helpers."""

from __future__ import annotations

import pytest

from core.nodes.critics import CritiqueReport
from core.nodes.planner import PlanResult
from core.policies import (
    merge_research_results,
    policy_retry_on_critic_failure,
    policy_retry_on_low_confidence,
    retry_tracker,
)
from core.state import State
from web.researcher_web import CitationResult


def test_policy_retry_on_low_confidence() -> None:
    """Planner with low confidence should trigger a retry."""

    assert policy_retry_on_low_confidence(PlanResult(confidence=0.5))
    assert not policy_retry_on_low_confidence(PlanResult(confidence=0.9))


def test_policy_retry_on_critic_failure() -> None:
    """Presence of issues should trigger a content rewrite."""

    assert policy_retry_on_critic_failure(CritiqueReport(issues=["gap"]))
    assert not policy_retry_on_critic_failure(CritiqueReport())


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
