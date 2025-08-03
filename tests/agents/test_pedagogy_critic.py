"""Tests for the pedagogy critic."""

import asyncio

from core.state import State

from agents.models import Activity
from agents.pedagogy_critic import (
    Outline,
    analyze_bloom_coverage,
    assess_cognitive_load,
    evaluate_activity_diversity,
    run_pedagogy_critic,
)


def build_outline():
    activities = [
        Activity(
            type="lecture",
            description="Intro to topic",
            duration_min=90,
            learning_objectives=["list facts"],
        ),
        Activity(
            type="lecture",
            description="Deep dive",
            duration_min=30,
            learning_objectives=["explain concept"],
        ),
        Activity(
            type="discussion",
            description="Group debate",
            duration_min=30,
            learning_objectives=["evaluate arguments"],
        ),
    ]
    return Outline(
        learning_objectives=["list facts", "explain concept"],
        activities=activities,
    )


def test_analyze_bloom_coverage_flags_missing_levels():
    outline = build_outline()
    report = analyze_bloom_coverage(outline)
    assert "apply" in report.missing_levels
    assert report.coverage_score < 1


def test_activity_diversity_identifies_dominance():
    outline = build_outline()
    report = evaluate_activity_diversity(outline)
    assert not report.is_balanced
    assert report.dominant_type == "lecture"


def test_assess_cognitive_load_spots_long_segment():
    outline = build_outline()
    report = assess_cognitive_load(outline)
    assert report.overloaded_segments == ["Intro to topic"]


def test_run_pedagogy_critic_compiles_reports():
    outline = build_outline()
    state = State()
    state.outline = outline
    critique = asyncio.run(run_pedagogy_critic(state))
    assert critique.bloom.missing_levels
    assert critique.recommendations


def test_analyze_bloom_coverage_accepts_custom_classifier():
    outline = build_outline()
    outline.learning_objectives.append("synthesize approach")

    def fake_classifier(text: str) -> str:
        return "create" if "synthesize" in text else "remember"

    report = analyze_bloom_coverage(outline, classifier=fake_classifier)
    assert "create" not in report.missing_levels
