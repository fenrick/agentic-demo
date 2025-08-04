import os

os.environ.setdefault("OPENAI_API_KEY", "x")
os.environ.setdefault("PERPLEXITY_API_KEY", "x")
os.environ.setdefault("DATA_DIR", "/tmp")

from agents import offline_cache
from agents.researcher_web import PerplexityClient, RawSearchResult


def test_search_hits_api_and_caches_results(monkeypatch, tmp_path):
    monkeypatch.setattr(offline_cache, "CACHE_DIR", tmp_path)

    class DummyLLM:
        def invoke(self, prompt: str):
            class Resp:
                content = ""
                additional_kwargs = {
                    "search_results": [
                        {
                            "url": "http://example.com",
                            "snippet": "snippet",
                            "title": "title",
                        }
                    ]
                }

            return Resp()

    tokens: list[str] = []
    debugs: list[str] = []
    import agents.researcher_web as rw

    monkeypatch.setattr(rw, "stream_messages", tokens.append)
    monkeypatch.setattr(rw, "stream_debug", debugs.append)

    client = PerplexityClient(api_key="token", llm=DummyLLM())
    results = client.search("hello world")

    assert results == [
        RawSearchResult(url="http://example.com", snippet="snippet", title="title")
    ]
    assert (tmp_path / "hello_world.json").exists()
    assert tokens == ["snippet"]
    assert debugs == ["perplexity search: hello world"]


def test_fallback_search_returns_cached(monkeypatch, tmp_path):
    monkeypatch.setattr(offline_cache, "CACHE_DIR", tmp_path)
    expected = [RawSearchResult(url="http://a", snippet="b", title="c")]
    offline_cache.save_cached_results("query", expected)

    tokens: list[str] = []
    debugs: list[str] = []
    import agents.researcher_web as rw

    monkeypatch.setattr(rw, "stream_messages", tokens.append)
    monkeypatch.setattr(rw, "stream_debug", debugs.append)

    client = PerplexityClient(api_key="token", llm=object())
    results = client.fallback_search("query")
    assert results == expected
    assert tokens == ["b"]
    assert debugs == ["offline search: query"]
