"""Researcher node invoking the web helper."""

from __future__ import annotations

from typing import List

from core.state import State
from web.researcher_web import CitationResult, researcher_web


async def run_researcher_web(state: State) -> List[CitationResult]:
    """Fire off web searches and return ranked snippets + metadata.

    TODO: Enhance with query generation and ranking algorithms.
    """

    urls = [c.url for c in state.sources]
    return await researcher_web(urls)
