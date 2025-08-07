"""Domain models for agent interactions."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Activity(BaseModel):
    """Learning activity performed during the lecture."""

    type: str
    description: str
    duration_min: int
    learning_objectives: list[str] = Field(default_factory=list)


class SlideBullet(BaseModel):
    """Bullet points associated with a slide."""

    slide_number: int
    bullets: list[str]


class AssessmentItem(BaseModel):
    """Assessment or quiz used to evaluate understanding."""

    type: str
    description: str
    max_score: float | None = None


class Citation(BaseModel):
    """Reference to an external source."""

    url: str
    title: str
    retrieved_at: str
    licence: str | None = None


class WeaveResult(BaseModel):
    """Typed container mirroring the weave schema output."""

    title: str
    learning_objectives: list[str]
    activities: list[Activity]
    duration_min: int
    author: str | None = None
    date: str | None = None
    version: str | None = None
    summary: str | None = None
    tags: list[str] | None = None
    prerequisites: list[str] | None = None
    slide_bullets: list[SlideBullet] | None = None
    speaker_notes: str | None = None
    assessment: list[AssessmentItem] | None = None
    references: list[Citation] | None = None
