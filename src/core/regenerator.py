"""Utilities for selective content regeneration based on critic feedback."""

from __future__ import annotations

from typing import List

from langgraph.graph.state import CompiledStateGraph

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


def apply_regeneration(
    graph: CompiledStateGraph[State], state: State, sections: List[SectionIdentifier]
) -> None:
    """Invoke the Content Weaver node for the specified sections."""
    for section_id in sections:
        try:
            idx = int(section_id)
        except ValueError:
            continue
        graph.invoke("Content-Weaver", state, section_id=idx)  # type: ignore[attr-defined]


def orchestrate_regeneration(
    state: State,
    report: CritiqueReport | FactCheckReport,
    graph: CompiledStateGraph[State] | None = None,
) -> State:
    """Select sections for rewriting and trigger regeneration.

    Args:
        state: Current application state.
        report: Critic or fact-checker output used to choose sections.
        graph: Optional LangGraph instance; if ``None`` the global orchestrator graph is used.

    Returns:
        Updated state after any regeneration triggers.
    """
    if graph is None:
        from core.orchestrator import graph as orchestrator_graph

        graph = orchestrator_graph

    sections = get_sections_to_regenerate(report)
    to_regenerate: List[SectionIdentifier] = []
    for section in sections:
        if has_exceeded_max_retries(state, section):
            continue
        increment_retry_count(state, section)
        to_regenerate.append(section)
    if to_regenerate:
        apply_regeneration(graph, state, to_regenerate)
    return state
