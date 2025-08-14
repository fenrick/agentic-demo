"""Domain models for agent interactions."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Activity(BaseModel):
    """Learning activity performed during the session."""

    type: str
    description: str
    duration_min: int
    learning_objectives: list[str] = Field(default_factory=list)


class SlideCopy(BaseModel):
    """Bullet points or short text shown on a slide."""

    bullet_points: list[str] = Field(default_factory=list)


class SlideVisualization(BaseModel):
    """Guidance on the visual elements for a slide."""

    notes: str


class SlideSpeakerNotes(BaseModel):
    """Narrative delivered by the speaker for a slide."""

    notes: str


class Slide(BaseModel):
    """Structured content for an individual slide."""

    slide_number: int
    copy: SlideCopy | None = None
    visualization: SlideVisualization | None = None
    speaker_notes: SlideSpeakerNotes | None = None


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


class ResearchResult(BaseModel):
    """Search result captured by the researcher."""

    url: str
    title: str
    snippet: str
    keywords: list[str] = Field(default_factory=list)


class LessonPlan(BaseModel):
    """Plan for a single lesson segment."""

    title: str
    bloom_level: str | None = None
    objectives: list[str] = Field(default_factory=list)


class EditorFeedback(BaseModel):
    """Feedback provided by the editor after reviewing content."""

    needs_revision: bool = False
    notes: str | None = None


class QAReport(BaseModel):
    """Outcome of the final quality review."""

    score: float
    notes: str | None = None


class WeaveResult(BaseModel):
    """Typed container representing a learning session.

    Attributes:
        title: Human readable session title.
        learning_objectives: Goals learners should achieve.
        duration_min: Expected duration in minutes.
        session_type: Delivery style such as "lecture" or "workshop".
        pedagogical_styles: Optional teaching approaches used.
        learning_methods: Optional learner engagement techniques.
        author: Name of session creator.
        date: Creation or delivery date.
        version: Version identifier.
        summary: High level overview of the session.
        tags: Keywords for discovery.
        prerequisites: Topics participants should know beforehand.
        slides: Ordered slide deck for delivery.
        assessment: Evaluative items to check understanding.
        references: Citations for external sources.
    """

    title: str
    learning_objectives: list[str]
    duration_min: int
    session_type: str = "lecture"
    pedagogical_styles: list[str] | None = None
    learning_methods: list[str] | None = None
    author: str | None = None
    date: str | None = None
    version: str | None = None
    summary: str | None = None
    tags: list[str] | None = None
    prerequisites: list[str] | None = None
    slides: list[Slide] | None = None
    assessment: list[AssessmentItem] | None = None
    references: list[Citation] | None = None
