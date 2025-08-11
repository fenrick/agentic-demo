"""State management models for core application logic."""

from __future__ import annotations

from dataclasses import field as dc_field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl
from pydantic.dataclasses import dataclass

from agents.models import Activity
from models import CritiqueReport, FactCheckReport


class Citation(BaseModel):
    """Reference to an external information source.

    Attributes:
        url: Location of the referenced material.
    """

    url: HttpUrl


class Module(BaseModel):
    """Discrete unit within a planned lecture."""

    id: str
    title: str
    duration_min: int
    learning_objectives: List[str] = Field(default_factory=list)
    activities: List[Activity] = Field(default_factory=list)


class Outline(BaseModel):
    """High-level structural outline for generated content.

    Attributes:
        steps: Ordered list describing the content flow.
        learning_objectives: Goals to achieve throughout the content.
        modules: Planned modules forming the outline.
    """

    steps: List[str] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)
    modules: List[Module] = Field(default_factory=list)

    @property
    def activities(self) -> List[Activity]:
        """Aggregate activities from all modules."""
        acts: List[Activity] = []
        for module in self.modules:
            acts.extend(module.activities)
        return acts


class ActionLog(BaseModel):
    """Record of an action taken during processing.

    Attributes:
        message: Human-readable description of the action.
        level: Severity level of the log entry.
        timestamp: Time when the action occurred.
    """

    message: str
    level: str = "INFO"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class State:
    """Represents the evolving application state.

    Attributes:
        prompt: Original user input that kicked off processing.
        sources: Collected citations from research steps.
        outline: Draft structure for the eventual output.
        log: List of actions performed so far.
        retries: Mapping of node name to how many times it has retried.
        retry_counts: Mapping of outline section identifiers to regeneration attempts.
        learning_objectives: Global objectives driving content generation.
        modules: Collection of planned content modules.
        critique_report: Feedback from pedagogical review.
        factcheck_report: Findings from factual verification.
        version: Monotonic revision number for persistence.
    """

    prompt: str = ""
    sources: List[Citation] = dc_field(default_factory=list)
    outline: Outline = dc_field(default_factory=Outline)
    log: List[ActionLog] = dc_field(default_factory=list)
    retries: Dict[str, int] = dc_field(default_factory=dict)
    retry_counts: Dict[str, int] = dc_field(default_factory=dict)
    learning_objectives: List[str] = dc_field(default_factory=list)
    modules: List[Module] = dc_field(default_factory=list)
    critique_report: Optional[CritiqueReport] = None
    factcheck_report: Optional[FactCheckReport] = None
    version: int = 1

    def __post_init__(self) -> None:
        """Validate basic invariants after initialization."""
        if not self.prompt:
            raise ValueError("prompt must be non-empty")
        urls = [src.url for src in self.sources]
        if len(urls) != len(set(urls)):
            raise ValueError("citation URLs must be unique")

    def to_dict(self) -> dict:
        """Serialize the current state into a plain dict for persistence.

        Returns:
            dict: Plain dictionary capturing the state values using only
            built-in types.
        """
        return {
            "prompt": self.prompt,
            "sources": [source.model_dump() for source in self.sources],
            "outline": self.outline.model_dump(),
            "log": [entry.model_dump() for entry in self.log],
            "retries": self.retries,
            "retry_counts": self.retry_counts,
            "learning_objectives": self.learning_objectives,
            "modules": [module.model_dump() for module in self.modules],
            "critique_report": (
                self.critique_report.model_dump() if self.critique_report else None
            ),
            "factcheck_report": (
                self.factcheck_report.model_dump() if self.factcheck_report else None
            ),
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
            outline=Outline(**raw["outline"]) if raw.get("outline") else Outline(),
            log=[ActionLog(**entry_data) for entry_data in raw.get("log", [])],
            retries=raw.get("retries", {}),
            retry_counts=raw.get("retry_counts", {}),
            learning_objectives=raw.get("learning_objectives", []),
            modules=[Module(**m) for m in raw.get("modules", [])],
            critique_report=(
                CritiqueReport(**raw["critique_report"])
                if raw.get("critique_report")
                else None
            ),
            factcheck_report=(
                FactCheckReport(**raw["factcheck_report"])
                if raw.get("factcheck_report")
                else None
            ),
            version=raw.get("version", 1),
        )  # type: ignore[call-arg]


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
        ValueError: If ``prompt`` is empty, citations
        are duplicated, or ``version`` is negative.
    """
    if not state.prompt:
        raise ValueError("prompt must be non-empty")
    if state.version < 0:
        raise ValueError("version must be non-negative")
    urls = [src.url for src in state.sources]
    if len(urls) != len(set(urls)):
        raise ValueError("citation URLs must be unique")


__all__ = [
    "Citation",
    "Module",
    "CritiqueReport",
    "FactCheckReport",
    "Outline",
    "ActionLog",
    "State",
    "increment_version",
    "validate_state",
]
