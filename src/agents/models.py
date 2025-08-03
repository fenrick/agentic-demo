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
class WeaveResult:
    """Typed container mirroring the weave schema output."""

    learning_objectives: List[str]
    activities: List[Activity]
    duration_min: int
    slide_bullets: Optional[List[SlideBullet]] = None
    speaker_notes: Optional[str] = None
