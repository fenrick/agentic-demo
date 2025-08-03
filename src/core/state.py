"""State management models for core application logic."""

from __future__ import annotations

from dataclasses import field as dc_field
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass


# TODO: Replace placeholder models with domain-specific implementations and
#       expand attributes such as titles and metadata.
class Citation(BaseModel):
    """Reference to an external information source.

    Attributes:
        url: Location of the referenced material.
    """

    url: str


# TODO: Support hierarchical outlines and richer step metadata.
class Outline(BaseModel):
    """High-level structural outline for generated content.

    Attributes:
        steps: Ordered list describing the content flow.
    """

    steps: List[str] = Field(default_factory=list)


# TODO: Extend to capture timestamps and log levels.
class ActionLog(BaseModel):
    """Record of an action taken during processing.

    Attributes:
        message: Human-readable description of the action.
    """

    message: str


@dataclass
class State:
    """Represents the evolving application state.

    Attributes:
        prompt: Original user input that kicked off processing.
        sources: Collected citations from research steps.
        outline: Draft structure for the eventual output.
        log: List of actions performed so far.
        version: Monotonic revision number for persistence.
    """

    # TODO: Add validation rules (e.g., non-empty prompt) once requirements are defined.
    prompt: str = ""
    # TODO: Ensure citations are unique and URLs valid.
    sources: List[Citation] = dc_field(default_factory=list)
    # TODO: Provide a sensible default outline when planner is implemented.
    outline: Optional[Outline] = None
    # TODO: Include structured log entries with metadata like timestamps.
    log: List[ActionLog] = dc_field(default_factory=list)
    # TODO: Revisit versioning strategy for future schema evolution.
    version: int = 1
