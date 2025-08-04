"""Client for the Perplexity search API with offline fallback."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import List, Protocol
from urllib.parse import urlparse

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
    """Wrapper around the Perplexity search endpoint."""

    endpoint = "https://api.perplexity.ai/search"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def search(self, query: str) -> List[RawSearchResult]:
        """Call the remote API and cache results."""
        payload = json.dumps({"q": query}).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        request = urllib.request.Request(
            self.endpoint, data=payload, headers=headers, method="POST"
        )
        with urllib.request.urlopen(request) as response:  # nosec B310
            data = json.loads(response.read().decode("utf-8"))
        results = [
            RawSearchResult(
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
                title=item.get("title", ""),
            )
            for item in data.get("search_results", [])
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
