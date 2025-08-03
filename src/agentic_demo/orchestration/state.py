"""Orchestration state models.

This module re-exports state-related models from :mod:`core.state` to
provide a stable import path for orchestration components.
"""

from core.state import ActionLog, Citation, Outline, State

__all__ = ["ActionLog", "Citation", "Outline", "State"]
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

"""Application state model used by orchestration graphs.

This module re-exports the core :class:`State` model so that orchestration
components can import it from a dedicated subpackage without creating a hard
dependency on the broader core package structure.
"""

from __future__ import annotations

from core.state import State

__all__ = ["State"]
