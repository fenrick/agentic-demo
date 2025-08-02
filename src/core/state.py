"""State management models for core application logic."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional


# TODO: Replace placeholder models with domain-specific implementations.
class Citation(BaseModel):
    """Reference to an external information source."""

    url: str


class Outline(BaseModel):
    """High-level structural outline for generated content."""

    steps: List[str] = Field(default_factory=list)


class ActionLog(BaseModel):
    """Record of an action taken during processing."""

    message: str


class State(BaseModel):
    """Represents the evolving application state."""

    # TODO: Expand fields as system capabilities grow.
    prompt: str = ""
    sources: List[Citation] = Field(default_factory=list)
    outline: Optional[Outline] = None
    log: List[ActionLog] = Field(default_factory=list)
    version: int = 1
