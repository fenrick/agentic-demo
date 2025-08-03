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

    def to_dict(self) -> dict:
        """Serialize the current state into a plain dict for persistence.

        Returns:
            dict: Plain dictionary capturing the state values using only
            built-in types.
        """
        return {
            "prompt": self.prompt,
            "sources": [source.model_dump() for source in self.sources],
            "outline": self.outline.model_dump() if self.outline else None,
            "log": [entry.model_dump() for entry in self.log],
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> "State":
        """Rehydrate a :class:`State` instance from a raw dictionary.

        Args:
            raw: Data previously produced by :meth:`to_dict`.

        Returns:
            State: New instance populated with ``raw`` values.
        """
        return cls(
            prompt=raw.get("prompt", ""),
            sources=[Citation(**c) for c in raw.get("sources", [])],
            outline=Outline(**raw["outline"]) if raw.get("outline") else None,
            log=[ActionLog(**entry_data) for entry_data in raw.get("log", [])],
            version=raw.get("version", 1),
        )


def increment_version(state: State) -> int:
    """Bump the version counter whenever a mutation is saved.

    Args:
        state: The state object whose version should be incremented.

    Returns:
        int: The incremented version number.
    """
    state.version += 1
    return state.version


def validate_state(state: State) -> None:
    """Quick sanity check before running the graph.

    Args:
        state: The state instance to validate.

    Raises:
        ValueError: If ``prompt`` is empty or ``version`` is negative.
    """
    if not state.prompt:
        raise ValueError("prompt must be non-empty")
    if state.version < 0:
        raise ValueError("version must be non-negative")
