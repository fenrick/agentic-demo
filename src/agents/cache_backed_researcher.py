"""Offline researcher using cached search results only."""

from __future__ import annotations

from typing import List

from .offline_cache import load_cached_results
from .researcher_web import RawSearchResult


class CacheBackedResearcher:
    """Return cached search results for a query.

    The researcher does not perform any network calls. It simply reads
    pre-fetched results from ``workspace/cache/{query}.json``. If no cache file
    is present the search fails immediately, signalling that the user must
    populate the cache beforehand.
    """

    def search(self, query: str) -> List[RawSearchResult]:
        """Load cached results for ``query`` or raise ``FileNotFoundError``.

        Parameters
        ----------
        query:
            The search phrase used to locate a cache file.

        Returns
        -------
        list[RawSearchResult]
            Previously cached search results.

        Raises
        ------
        FileNotFoundError
            If no cache file exists for ``query``.
        """

        results = load_cached_results(query)
        if results is None:
            raise FileNotFoundError(f"No cached results for query '{query}'")
        return results
