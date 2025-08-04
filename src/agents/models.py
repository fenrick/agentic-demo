"""Domain models for agent interactions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(slots=True)
class Activity:
    """Learning activity performed during the lecture."""

    type: str
    description: str
    duration_min: int
    learning_objectives: List[str] = field(default_factory=list)


@dataclass(slots=True)
class SlideBullet:
    """Bullet points associated with a slide."""

    slide_number: int
    bullets: List[str]


@dataclass(slots=True)
class AssessmentItem:
    """Assessment or quiz used to evaluate understanding."""

    type: str
    description: str
    max_score: Optional[float] = None


@dataclass(slots=True)
class Citation:
    """Reference to an external source."""

    url: str
    title: str
    retrieved_at: str
    licence: Optional[str] = None


@dataclass(slots=True)
class WeaveResult:
    """Typed container mirroring the weave schema output."""

    title: str
    learning_objectives: List[str]
    activities: List[Activity]
    duration_min: int
    author: Optional[str] = None
    date: Optional[str] = None
    version: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    slide_bullets: Optional[List[SlideBullet]] = None
    speaker_notes: Optional[str] = None
    assessment: Optional[List[AssessmentItem]] = None
    references: Optional[List[Citation]] = None
