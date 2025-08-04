"""Tests for the cache-backed researcher."""

import pytest

from agents.cache_backed_researcher import CacheBackedResearcher


def test_cache_backed_researcher_raises_on_missing_cache():
    researcher = CacheBackedResearcher()
    with pytest.raises(FileNotFoundError):
        researcher.search("query-with-no-cache")
