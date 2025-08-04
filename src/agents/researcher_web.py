"""Client for the Perplexity Sonar API with offline fallback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Protocol
from urllib.parse import urlparse

from langchain_perplexity import ChatPerplexity

from .offline_cache import load_cached_results, save_cached_results


@dataclass(slots=True)
class RawSearchResult:
    """Minimal search result returned by Perplexity."""

    url: str
    snippet: str
    title: str


@dataclass(slots=True)
class CitationDraft:
    """Preliminary citation information used during filtering."""

    url: str
    snippet: str
    title: str


class PerplexityClient:
    """Wrapper around the Perplexity Sonar model via LangChain."""

    def __init__(self, api_key: str, llm: Optional[Any] = None) -> None:
        self.llm = llm or ChatPerplexity(model="sonar", pplx_api_key=api_key)

    def search(self, query: str) -> List[RawSearchResult]:
        """Call the Sonar model and cache its cited search results."""
        response = self.llm.invoke(query)
        items = response.additional_kwargs.get("search_results", [])
        results = [
            RawSearchResult(
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
                title=item.get("title", ""),
            )
            for item in items
        ]
        save_cached_results(query, results)
        return results

    def fallback_search(self, query: str) -> List[RawSearchResult]:
        """Load cached results when offline."""
        return load_cached_results(query) or []


class ResearcherWebClient(Protocol):
    """Protocol for search clients used by the web researcher."""

    def search(self, query: str) -> List[RawSearchResult]:
        """Return search results for ``query``."""


def score_domain_authority(domain: str) -> float:
    """Return a simple authority score for ``domain``."""

    domain = domain.lower()
    if domain.endswith(".gov") or domain.endswith(".edu"):
        return 1.0
    if domain.endswith(".org"):
        return 0.8
    return 0.5


def rank_by_authority(results: List[CitationDraft]) -> List[CitationDraft]:
    """Sort drafts by descending domain authority."""

    def _score(draft: CitationDraft) -> float:
        domain = urlparse(draft.url).netloc
        return score_domain_authority(domain)

    return sorted(results, key=_score, reverse=True)
