"""Critic nodes for pedagogy and factual accuracy."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.state import State
from models import CritiqueReport
from .pedagogy_critic import run_pedagogy_critic


@dataclass(slots=True)
class FactCheckReport:
    """Report from the fact checker."""

    issues: list[str] = field(default_factory=list)


async def run_fact_checker(state: State) -> FactCheckReport:
    """Flag potential hallucinations.

    TODO: Implement real fact-checking logic.
    """

    return FactCheckReport()


__all__ = [
    "run_pedagogy_critic",
    "run_fact_checker",
    "CritiqueReport",
    "FactCheckReport",
]
