"""State model for orchestration tasks."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class State(BaseModel):
    """Represents the evolving orchestration state."""

    prompt: str = ""
    sources: List[str] = Field(default_factory=list)
    outline: List[str] = Field(default_factory=list)
    log: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    critic_attempts: int = 0
    critic_score: float = 0.0
