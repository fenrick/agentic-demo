"""Utilities for selective content regeneration based on critic feedback."""

from __future__ import annotations

from typing import List

from agents.content_weaver import run_content_weaver
from core.orchestrator import GraphOrchestrator, build_main_flow
from core.state import State
from models.critique_report import CritiqueReport
from models.fact_check_report import FactCheckReport

SectionIdentifier = str
MAX_RETRIES = 3


def get_sections_to_regenerate(
    report: CritiqueReport | FactCheckReport,
) -> List[SectionIdentifier]:
    """Extract identifiers for outline sections requiring regeneration.

    Args:
        report: Feedback report from a critic or fact checker.

    Returns:
        List of section identifiers derived from the report contents.
    """
    if isinstance(report, CritiqueReport):
        return list(report.cognitive_load.overloaded_segments)

    sections = {str(h.line_number) for h in report.hallucinations}
    sections.update(str(c.line_number) for c in report.unsupported_claims)
    return sorted(sections)


def increment_retry_count(state: State, section_id: SectionIdentifier) -> None:
    """Increment the retry counter for a specific section."""
    state.retry_counts[section_id] = state.retry_counts.get(section_id, 0) + 1


def has_exceeded_max_retries(state: State, section_id: SectionIdentifier) -> bool:
    """Determine whether a section has hit the retry limit."""
    return state.retry_counts.get(section_id, 0) >= MAX_RETRIES


async def apply_regeneration(state: State, sections: List[SectionIdentifier]) -> None:
    """Invoke ``run_content_weaver`` for the specified sections."""
    for section_id in sections:
        try:
            idx = int(section_id)
        except ValueError:
            continue
        await run_content_weaver(state, section_id=idx)


async def orchestrate_regeneration(
    state: State, report: CritiqueReport | FactCheckReport
) -> State:
    """Select sections for rewriting and trigger regeneration.

    Args:
        state: Current application state.
        report: Critic or fact-checker output used to choose sections.

    Returns:
        Updated state after any regeneration triggers.
    """
    sections = get_sections_to_regenerate(report)
    to_regenerate: List[SectionIdentifier] = []
    for section in sections:
        if has_exceeded_max_retries(state, section):
            continue
        increment_retry_count(state, section)
        to_regenerate.append(section)
    if not to_regenerate:
        return state

    await apply_regeneration(state, to_regenerate)

    flow = build_main_flow()
    start_idx = next(
        (i for i, node in enumerate(flow) if node.name == "Editor"),
        None,
    )
    if start_idx is not None:
        regen_flow = flow[start_idx:]
        await GraphOrchestrator(regen_flow).run(state)
    return state
