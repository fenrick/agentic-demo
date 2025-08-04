"""Researcher node delegating to the researcher pipeline."""

from __future__ import annotations

from typing import List

from agents.researcher_pipeline import researcher_pipeline
from core.state import Citation as StateCitation
from core.state import State


async def run_researcher_web(state: State) -> List[StateCitation]:
    """Execute the web research pipeline and update state sources."""

    citations = await researcher_pipeline(state.prompt, state)
    new_sources = [StateCitation(url=c.url) for c in citations]
    state.sources.extend(new_sources)
    return new_sources
