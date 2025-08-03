import json
import urllib.request

from agents import offline_cache
from agents.researcher_web import PerplexityClient, RawSearchResult


def test_search_hits_api_and_caches_results(monkeypatch, tmp_path):
    monkeypatch.setattr(offline_cache, "CACHE_DIR", tmp_path)

    payload = {
        "search_results": [
            {"url": "http://example.com", "snippet": "snippet", "title": "title"}
        ]
    }

    class DummyResponse:
        def read(self):
            return json.dumps(payload).encode("utf-8")

        def __enter__(self):  # pragma: no cover - trivial
            return self

        def __exit__(self, *exc):  # pragma: no cover - trivial
            return None

    monkeypatch.setattr(urllib.request, "urlopen", lambda req: DummyResponse())

    client = PerplexityClient(api_key="token")
    results = client.search("hello world")

    assert results == [
        RawSearchResult(url="http://example.com", snippet="snippet", title="title")
    ]
    assert (tmp_path / "hello_world.json").exists()


def test_fallback_search_returns_cached(monkeypatch, tmp_path):
    monkeypatch.setattr(offline_cache, "CACHE_DIR", tmp_path)
    expected = [RawSearchResult(url="http://a", snippet="b", title="c")]
    offline_cache.save_cached_results("query", expected)

    client = PerplexityClient(api_key="token")
    results = client.fallback_search("query")
    assert results == expected
