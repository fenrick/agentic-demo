"""Planner node producing a high-level plan for the run."""

from __future__ import annotations

from dataclasses import dataclass

from core.state import Outline, State


@dataclass(slots=True)
class PlanResult:
    """Outcome of the planner step."""

    outline: Outline | None = None
    confidence: float = 0.0


async def run_planner(state: State) -> PlanResult:
    """Analyze ``state.prompt`` and draft an outline.

    TODO: Implement real planning logic with language model calls and
    learning goal extraction.
    """

    # Placeholder: echo existing outline with dummy confidence.
    return PlanResult(outline=state.outline, confidence=0.0)
