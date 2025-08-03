"""Edge policies and retry utilities for the orchestrator."""

from __future__ import annotations

from typing import List
from urllib.parse import urlparse

from agents.critics import CritiqueReport, FactCheckReport
from agents.planner import PlanResult
from core.state import Citation, State
from web.researcher_web import CitationResult


def policy_retry_on_low_confidence(prev: PlanResult, threshold: float = 0.8) -> bool:
    """Return ``True`` when planner confidence is below ``threshold``.

    Args:
        prev: Result object emitted by the planner node.
        threshold: Minimum acceptable confidence before progressing.

    Returns:
        ``True`` if the planner should hand control back to the researcher,
        ``False`` otherwise.
    """

    return prev.confidence < threshold


def policy_retry_on_critic_failure(
    report: CritiqueReport | FactCheckReport,
) -> bool:
    """Determine whether content must be regenerated after critic review.

    Args:
        report: Outcome from either the pedagogy critic or fact checker.

    Returns:
        ``True`` when issues were flagged and the content weaver should be
        reinvoked, ``False`` when critique passes.
    """

    return bool(report.issues)


def merge_research_results(results: List[CitationResult]) -> List[Citation]:
    """Deduplicate and rank researcher web results.

    Args:
        results: List of raw :class:`CitationResult` objects from parallel
            web searches.

    Returns:
        A list of unique :class:`Citation` instances preserving the first
        occurrence order. URLs are canonicalized to avoid duplicates differing
        only by scheme or trailing slashes.
    """

    seen: set[str] = set()
    merged: list[Citation] = []
    for item in results:
        parsed = urlparse(item.url)
        key = f"{parsed.netloc.lower()}{parsed.path.rstrip('/').lower()}"
        if key in seen:
            continue
        seen.add(key)
        merged.append(Citation(url=item.url))
    return merged


def retry_tracker(state: State, agent_name: str) -> int:
    """Increment and validate retry count for ``agent_name``.

    Args:
        state: Mutable state carrying retry counters.
        agent_name: Name of the node invoking a retry.

    Returns:
        int: The updated retry count for ``agent_name``.

    Raises:
        RuntimeError: If the retry limit of three is exceeded.
    """

    count = state.retries.get(agent_name, 0)
    if count >= 3:
        raise RuntimeError(f"Retry limit exceeded for {agent_name}")
    count += 1
    state.retries[agent_name] = count
    return count


__all__ = [
    "policy_retry_on_low_confidence",
    "policy_retry_on_critic_failure",
    "merge_research_results",
    "retry_tracker",
]
