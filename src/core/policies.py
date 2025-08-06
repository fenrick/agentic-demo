"""Edge policies and retry utilities for the orchestrator."""

from __future__ import annotations

from typing import List, Literal
from urllib.parse import urlparse

from agents.critics import CritiqueReport, FactCheckReport
from agents.planner import PlanResult
from core.state import Citation, State
from web.researcher_web import CitationResult


def policy_retry_on_low_confidence(
    prev: PlanResult,
    state: State,
    threshold: float = 0.8,
    *,
    agent_name: str = "Planner",
) -> Literal["loop", "continue"]:
    """Decide whether to loop back for more research or continue planning.

    This policy consults the retry tracker to enforce a maximum of three
    retries. When planner confidence falls below ``threshold`` the function
    allows another research cycle only if the retry count has not been
    exhausted. Once the limit is reached the workflow proceeds without raising
    an error.

    Args:
        prev: Result object emitted by the planner node.
        state: Mutable application state for tracking retries.
        threshold: Minimum acceptable confidence before progressing.
        agent_name: Identifier passed to :func:`retry_tracker`.

    Returns:
        ``"loop"`` if the planner should hand control back to the researcher,
        ``"continue"`` when the planner may proceed forward.
    """

    should_loop = prev.confidence < threshold
    if should_loop:
        try:
            retry_tracker(state, agent_name)
        except RuntimeError:
            should_loop = False
    return "loop" if should_loop else "continue"


def policy_retry_on_critic_failure(
    report: CritiqueReport | FactCheckReport,
    state: State,
    *,
    agent_name: str = "Content-Weaver",
) -> bool:
    """Determine whether content must be regenerated after critic review.

    The retry tracker ensures the content weaver is not reinvoked more than
    three times. Exceeding this limit raises a :class:`RuntimeError` which
    should terminate the workflow.

    Args:
        report: Outcome from either the pedagogy critic or fact checker.
        state: Mutable application state for tracking retries.
        agent_name: Identifier passed to :func:`retry_tracker`.

    Returns:
        ``True`` when recommendations or factual issues were flagged and the
        content weaver should be reinvoked, ``False`` when critique passes.
    """

    if isinstance(report, CritiqueReport):
        should_retry = bool(report.recommendations)
    else:
        should_retry = bool(
            report.hallucination_count or report.unsupported_claims_count
        )
    if should_retry:
        retry_tracker(state, agent_name)
    return should_retry


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
