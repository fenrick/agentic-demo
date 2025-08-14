"""Agent that performs the final quality assessment."""

from __future__ import annotations

from core.state import State

from .models import QAReport


async def run_final_reviewer(state: State) -> QAReport:
    """Assign a quality score to the generated materials.

    The stub implementation assigns a perfect score and stores the report on
    the provided ``state`` instance.
    """

    report = QAReport(score=1.0)
    state.qa_report = report
    return report


__all__ = ["run_final_reviewer"]
