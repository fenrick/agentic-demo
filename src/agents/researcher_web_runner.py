"""Entry point for performing a web search based on state."""

from __future__ import annotations

from typing import List

from config import Settings
from core.state import State

from .cache_backed_researcher import CacheBackedResearcher
from .researcher_web import (
    CitationDraft,
    PerplexityClient,
    RawSearchResult,
    SearchClient,
    TavilyClient,
)


def _to_draft(result: RawSearchResult) -> CitationDraft:
    return CitationDraft(url=result.url, snippet=result.snippet, title=result.title)


def run_web_search(state: State) -> List[CitationDraft]:
    """Run a web search using the configured provider."""
    settings = Settings()
    if settings.offline_mode:
        client: SearchClient = CacheBackedResearcher()
    elif settings.search_provider == "tavily":
        client = TavilyClient(settings.tavily_api_key or "")
    else:
        client = PerplexityClient(settings.perplexity_api_key)
    results = client.search(state.prompt)
    return [_to_draft(r) for r in results]
