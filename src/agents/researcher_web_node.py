"""Researcher node delegating to the researcher pipeline."""

from __future__ import annotations

import re
from typing import List

from agents.models import ResearchResult
from agents.researcher_pipeline import researcher_pipeline
from agents.researcher_web_runner import run_web_search
from core.state import Citation as StateCitation
from core.state import State


def _extract_keywords(text: str) -> list[str]:
    """Return unique keywords from ``text``."""

    words = re.findall(r"\b\w+\b", text.lower())
    return sorted({w for w in words if len(w) > 3})


async def run_researcher_web(state: State) -> List[ResearchResult]:
    """Execute web research and record results with keywords."""

    drafts = await run_web_search(state)
    results: List[ResearchResult] = []
    for draft in drafts:
        text = f"{draft.title} {draft.snippet}"
        keywords = _extract_keywords(text)
        results.append(
            ResearchResult(
                url=draft.url,
                title=draft.title,
                snippet=draft.snippet,
                keywords=keywords,
            )
        )
    state.research_results.extend(results)

    citations = await researcher_pipeline(state.prompt, state)
    new_sources = [StateCitation(url=c.url) for c in citations]
    state.sources.extend(new_sources)
    return results
