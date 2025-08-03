"""Critic nodes for pedagogy and factual accuracy."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.state import State


@dataclass(slots=True)
class CritiqueReport:
    """Report from the pedagogy critic."""

    issues: list[str] = field(default_factory=list)


async def run_pedagogy_critic(state: State) -> CritiqueReport:
    """Validate pedagogy coverage.

    TODO: Implement real critique logic.
    """

    return CritiqueReport()


@dataclass(slots=True)
class FactCheckReport:
    """Report from the fact checker."""

    issues: list[str] = field(default_factory=list)


async def run_fact_checker(state: State) -> FactCheckReport:
    """Flag potential hallucinations.

    TODO: Implement real fact-checking logic.
    """

    return FactCheckReport()
