"""Agent that translates planning intent into lesson plans."""

from __future__ import annotations

from core.state import State

from .models import LessonPlan


async def run_learning_advisor(state: State) -> list[LessonPlan]:
    """Generate lesson plans from the planner's modules.

    The current implementation returns an empty list and stores it on the
    provided ``state`` object.
    """

    plans: list[LessonPlan] = []
    state.lesson_plans = plans
    return plans


__all__ = ["run_learning_advisor"]
