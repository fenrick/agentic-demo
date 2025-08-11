"""Data models for fact checking reports."""

from __future__ import annotations

from dataclasses import asdict, field
from typing import Any, Dict, List, Union

from pydantic.dataclasses import dataclass


@dataclass(slots=True)
class SentenceProbability:
    """Confidence score for a sentence."""

    line_number: int
    sentence: str
    probability: float


@dataclass(slots=True)
class ClaimFlag:
    """Marker for a potential unsupported claim."""

    line_number: int
    snippet: str


@dataclass(slots=True)
class FactCheckReport:
    """Aggregated fact-checking results."""

    hallucinations: List[SentenceProbability] = field(default_factory=list)
    unsupported_claims: List[ClaimFlag] = field(default_factory=list)
    hallucination_count: int = 0
    unsupported_claims_count: int = 0

    @property
    def issues(self) -> List[Union[SentenceProbability, ClaimFlag]]:
        """Combined list of detected factual issues."""

        return [*self.hallucinations, *self.unsupported_claims]

    def model_dump(self) -> Dict[str, Any]:
        """Return a serializable representation of the report."""
        return asdict(self)  # type: ignore[arg-type, call-overload]


__all__ = [
    "SentenceProbability",
    "ClaimFlag",
    "FactCheckReport",
]
