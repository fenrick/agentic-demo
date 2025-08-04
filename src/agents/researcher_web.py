"""Client for the Perplexity Sonar API with offline fallback."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict, dataclass
from typing import Any, List, Optional, Protocol
from urllib.parse import urlparse

from persistence import get_db_session
from persistence.repositories.retrieval_cache_repo import RetrievalCacheRepo

from .agent_wrapper import init_chat_model
from .dense_retriever import DenseRetriever
from .offline_cache import load_cached_results, save_cached_results
from .streaming import stream_debug, stream_messages


@dataclass(slots=True)
class RawSearchResult:
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

    def search(self, query: str) -> List[RawSearchResult]:
        """Return search results for ``query``."""


class PerplexityClient(SearchClient):
    """Wrapper around the Perplexity Sonar model via LangChain."""

    def __init__(self, api_key: str, llm: Optional[Any] = None) -> None:
        model = llm or init_chat_model(model="sonar", pplx_api_key=api_key)
        if model is None:  # pragma: no cover - dependency missing
            raise RuntimeError("Perplexity chat model unavailable")
        self.llm = model

    def search(self, query: str) -> List[RawSearchResult]:
        """Call the Sonar model and cache its cited search results."""

        stream_debug(f"perplexity search: {query}")
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
        for res in results:
            stream_messages(res.snippet)
        save_cached_results(query, results)
        return results

    def fallback_search(self, query: str) -> List[RawSearchResult]:
        """Load cached results when offline."""

        stream_debug(f"offline search: {query}")
        results = load_cached_results(query) or []
        for res in results:
            stream_messages(res.snippet)
        return results


class TavilyClient(SearchClient):
    """Client using Tavily web search via ``langchain_community``."""

    def __init__(self, api_key: str, wrapper: Optional[Any] = None) -> None:
        if wrapper is None:
            try:  # pragma: no cover - optional dependency
                from langchain_community.utilities.tavily_search import (
                    TavilySearchAPIWrapper,
                )
            except Exception as exc:  # pragma: no cover - dependency missing
                raise RuntimeError("Tavily search unavailable") from exc
            self.wrapper = TavilySearchAPIWrapper(tavily_api_key=api_key)
        else:
            self.wrapper = wrapper

    def search(self, query: str) -> List[RawSearchResult]:
        """Call the Tavily API and cache search results."""

        stream_debug(f"tavily search: {query}")
        items = self.wrapper.results(query)
        results = [
            RawSearchResult(
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                title=item.get("title", ""),
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
            return [RawSearchResult(**item) for item in cached]

    try:
        results = client.search(query)
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
        await repo.set(query, [asdict(r) for r in results])

    return results


def cached_search(
    query: str, client: SearchClient, dense: Optional[DenseRetriever] = None
) -> List[RawSearchResult]:
    """Synchronous wrapper around :func:`_cached_search_async`."""

    return asyncio.run(_cached_search_async(query, client, dense))


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
