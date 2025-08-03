"""Entry point for performing a web search based on state."""

from __future__ import annotations

from typing import List

from config import Settings
from core.state import State

from .researcher_web import CitationDraft, PerplexityClient, RawSearchResult


def _to_draft(result: RawSearchResult) -> CitationDraft:
    return CitationDraft(url=result.url, snippet=result.snippet, title=result.title)


def run_web_search(state: State) -> List[CitationDraft]:
    """Run a Perplexity search using the state's prompt as query."""
    settings = Settings()
    client = PerplexityClient(settings.perplexity_api_key)
    if settings.offline_mode:
        results = client.fallback_search(state.prompt)
    else:
        results = client.search(state.prompt)
    return [_to_draft(r) for r in results]
