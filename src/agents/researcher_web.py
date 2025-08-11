"""HTTP clients and utilities for researcher web search."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional, Protocol
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel

from persistence import get_db_session
from persistence.repositories.retrieval_cache_repo import RetrievalCacheRepo

from .dense_retriever import DenseRetriever
from .offline_cache import save_cached_results
from .streaming import stream_debug, stream_messages


class RawSearchResult(BaseModel):
    """Minimal search result returned by a search provider."""

    url: str
    snippet: str
    title: str


@dataclass(slots=True)
class CitationDraft:
    """Preliminary citation information used during filtering."""

    url: str
    snippet: str
    title: str


class SearchClient(Protocol):
    """Protocol for search clients used by the web researcher."""

    async def __aenter__(self) -> "SearchClient":  # pragma: no cover - protocol
        ...

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - protocol
        ...

    async def aclose(self) -> None:
        """Close any open resources."""

    async def search(self, query: str) -> List[RawSearchResult]:
        """Return search results for ``query``."""


class TavilyClient(SearchClient):
    """HTTPX client for the Tavily search API."""

    _URL = "https://api.tavily.com/search"

    def __init__(self, api_key: str, http: Optional[httpx.AsyncClient] = None) -> None:
        self._api_key = api_key
        self._http = http or httpx.AsyncClient(timeout=30)

    async def __aenter__(self) -> "TavilyClient":
        return self

    async def __aexit__(
        self, exc_type, exc, tb
    ) -> None:  # noqa: D401 - Protocol method
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""

        await self._http.aclose()

    async def search(self, query: str) -> List[RawSearchResult]:
        """Call the Tavily API and cache search results."""

        stream_debug(f"tavily search: {query}")
        response = await self._http.post(
            self._URL,
            json={"api_key": self._api_key, "query": query},
        )
        response.raise_for_status()
        items = response.json().get("results", [])
        results = [
            RawSearchResult.model_validate(
                {
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                    "title": item.get("title", ""),
                }
            )
            for item in items
        ]
        for res in results:
            stream_messages(res.snippet)
        save_cached_results(query, results)
        return results


async def _cached_search_async(
    query: str,
    client: SearchClient,
    dense: Optional[DenseRetriever] = None,
) -> List[RawSearchResult]:
    """Search ``query`` using ``client`` with caching and dense fallback."""

    async with get_db_session() as conn:
        repo = RetrievalCacheRepo(conn)
        cached = await repo.get(query)
        if cached is not None:
            stream_debug(f"cache hit: {query}")
            return [RawSearchResult.model_validate(item) for item in cached]

    try:
        results = await client.search(query)
    except Exception:
        logging.exception("Search client failed")
        if dense is None:
            raise
        stream_debug(f"dense retrieval fallback: {query}")
        results = dense.search(query)

    if not results and dense is not None:
        stream_debug(f"dense retrieval fallback: {query}")
        results = dense.search(query)

    async with get_db_session() as conn:
        repo = RetrievalCacheRepo(conn)
        await repo.set(query, [r.model_dump() for r in results])

    return results


async def cached_search(
    query: str, client: SearchClient, dense: Optional[DenseRetriever] = None
) -> List[RawSearchResult]:
    """Return cached search results for ``query`` using ``client``."""

    return await _cached_search_async(query, client, dense)


def cached_search_sync(
    query: str, client: SearchClient, dense: Optional[DenseRetriever] = None
) -> List[RawSearchResult]:
    """Synchronous wrapper around :func:`cached_search`.

    Raises ``RuntimeError`` if called when an event loop is already running.
    """

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(cached_search(query, client, dense))
    raise RuntimeError(
        "cached_search_sync cannot be used when an event loop is running; use 'await"
        " cached_search'"
    )


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
