"""Data classes representing outputs from the pedagogy critic."""

from __future__ import annotations

from dataclasses import field
from typing import Dict, List, Optional

from pydantic.dataclasses import dataclass


@dataclass(slots=True)
class BloomCoverageReport:
    """Coverage of Bloom's taxonomy levels."""

    level_counts: Dict[str, int]
    missing_levels: List[str]
    coverage_score: float


@dataclass(slots=True)
class ActivityDiversityReport:
    """Distribution of learning activity types."""

    type_percentages: Dict[str, float]
    is_balanced: bool
    dominant_type: Optional[str] = None


@dataclass(slots=True)
class CognitiveLoadReport:
    """Summary of estimated cognitive load for an outline."""

    total_duration: int
    overloaded_segments: List[str] = field(default_factory=list)


@dataclass(slots=True)
class CritiqueReport:
    """Aggregate of the pedagogy critic sub-reports."""

    bloom: BloomCoverageReport
    diversity: ActivityDiversityReport
    cognitive_load: CognitiveLoadReport
    recommendations: List[str] = field(default_factory=list)

    @property
    def issues(self) -> List[str]:
        """List of actionable recommendations for remediation."""

        return self.recommendations


__all__ = [
    "BloomCoverageReport",
    "ActivityDiversityReport",
    "CognitiveLoadReport",
    "CritiqueReport",
]
