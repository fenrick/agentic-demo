"""Pedagogical critic assessing outlines against teaching best practices."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, cast

from core.state import State

from agents.models import Activity
from models import (
    ActivityDiversityReport,
    BloomCoverageReport,
    CognitiveLoadReport,
    CritiqueReport,
)

# Bloom's taxonomy levels used for coverage analysis
BLOOM_LEVELS: List[str] = [
    "remember",
    "understand",
    "apply",
    "analyze",
    "evaluate",
    "create",
]

# Naive verb to level mapping for objective classification
_VERB_MAP: Dict[str, str] = {
    "list": "remember",
    "define": "remember",
    "describe": "understand",
    "explain": "understand",
    "use": "apply",
    "apply": "apply",
    "compare": "analyze",
    "analyze": "analyze",
    "evaluate": "evaluate",
    "critique": "evaluate",
    "create": "create",
    "design": "create",
}


@dataclass(slots=True)
class Outline:
    """Simple course outline used by the pedagogy critic."""

    learning_objectives: List[str]
    activities: List[Activity]


def _classify_text(text: str) -> str:
    """Map ``text`` to a Bloom level based on keyword matching."""

    lowered = text.lower()
    for verb, level in _VERB_MAP.items():
        if verb in lowered:
            return level
    return "unknown"


def analyze_bloom_coverage(outline: Outline) -> BloomCoverageReport:
    """Assess breadth of Bloom taxonomy coverage for an outline."""

    counts: Dict[str, int] = {level: 0 for level in BLOOM_LEVELS}
    for objective in outline.learning_objectives:
        level = _classify_text(objective)
        if level in counts:
            counts[level] += 1
    for act in outline.activities:
        for obj in act.learning_objectives:
            level = _classify_text(obj)
            if level in counts:
                counts[level] += 1
    covered = {lvl for lvl, cnt in counts.items() if cnt > 0}
    missing = [lvl for lvl in BLOOM_LEVELS if lvl not in covered]
    score = len(covered) / len(BLOOM_LEVELS)
    return BloomCoverageReport(
        level_counts=counts, missing_levels=missing, coverage_score=score
    )


def evaluate_activity_diversity(outline: Outline) -> ActivityDiversityReport:
    """Check for variety across activity types."""

    counts = Counter(act.type for act in outline.activities)
    total = sum(counts.values()) or 1
    percentages = {typ: count / total for typ, count in counts.items()}
    dominant = None
    balanced = True
    for typ, pct in percentages.items():
        if pct > 0.5:
            dominant = typ
            balanced = False
            break
    return ActivityDiversityReport(
        type_percentages=percentages, is_balanced=balanced, dominant_type=dominant
    )


def assess_cognitive_load(outline: Outline) -> CognitiveLoadReport:
    """Estimate cognitive load based on activity durations."""

    total = sum(act.duration_min for act in outline.activities)
    overloaded = [
        act.description for act in outline.activities if act.duration_min > 45
    ]
    return CognitiveLoadReport(total_duration=total, overloaded_segments=overloaded)


def run_pedagogy_critic(state: State) -> CritiqueReport:
    """Orchestrate pedagogical checks against the current state outline."""

    outline = cast(Outline, state.outline)
    if outline is None:
        raise ValueError("state.outline is required for pedagogy critique")
    bloom = analyze_bloom_coverage(outline)
    diversity = evaluate_activity_diversity(outline)
    cognitive = assess_cognitive_load(outline)
    recommendations: List[str] = []
    if bloom.missing_levels:
        recommendations.append(
            "cover additional Bloom levels: " + ", ".join(bloom.missing_levels)
        )
    if not diversity.is_balanced and diversity.dominant_type:
        recommendations.append(
            f"balance activities; too much {diversity.dominant_type}"
        )
    if cognitive.overloaded_segments:
        recommendations.append(
            "reduce cognitive load in segments: "
            + ", ".join(cognitive.overloaded_segments)
        )
    return CritiqueReport(
        bloom=bloom,
        diversity=diversity,
        cognitive_load=cognitive,
        recommendations=recommendations,
    )
