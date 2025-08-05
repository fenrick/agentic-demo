import asyncio
import os
import sys
import types

os.environ.setdefault("OPENAI_API_KEY", "x")
os.environ.setdefault("PERPLEXITY_API_KEY", "x")
os.environ.setdefault("TAVILY_API_KEY", "x")
os.environ.setdefault("DATA_DIR", "/tmp")

import config  # noqa: E402

pkg = types.ModuleType("agentic_demo")
pkg.config = config
sys.modules["agentic_demo"] = pkg
sys.modules["agentic_demo.config"] = config

from agents import offline_cache  # noqa: E402
from agents.dense_retriever import DenseRetriever  # noqa: E402
from agents.researcher_web import PerplexityClient  # noqa: E402
from agents.researcher_web import (  # noqa: E402
    RawSearchResult,
    TavilyClient,
    cached_search,
)
from persistence import get_db_session  # noqa: E402


def test_perplexity_search_hits_api_and_caches_results(monkeypatch, tmp_path):
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


def test_perplexity_fallback_search_returns_cached(monkeypatch, tmp_path):
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


def test_tavily_search_hits_api_and_caches_results(monkeypatch, tmp_path):
    monkeypatch.setattr(offline_cache, "CACHE_DIR", tmp_path)

    class DummyWrapper:
        def results(self, query: str):
            return [
                {
                    "url": "http://example.com",
                    "content": "snippet",
                    "title": "title",
                }
            ]

    tokens: list[str] = []
    debugs: list[str] = []
    import agents.researcher_web as rw

    monkeypatch.setattr(rw, "stream_messages", tokens.append)
    monkeypatch.setattr(rw, "stream_debug", debugs.append)

    client = TavilyClient(api_key="token", wrapper=DummyWrapper())
    results = client.search("hello world")

    assert results == [
        RawSearchResult(url="http://example.com", snippet="snippet", title="title")
    ]
    assert (tmp_path / "hello_world.json").exists()
    assert tokens == ["snippet"]
    assert debugs == ["tavily search: hello world"]


CREATE_CACHE_SQL = """
CREATE TABLE retrieval_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT UNIQUE NOT NULL,
    results TEXT NOT NULL,
    hit_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
)
"""


def test_cached_search_uses_retrieval_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    async def init_db() -> None:
        async with get_db_session() as conn:
            await conn.execute(CREATE_CACHE_SQL)
            await conn.commit()

    asyncio.run(init_db())

    class DummyClient:
        def __init__(self) -> None:
            self.calls = 0

        def search(self, query: str):
            self.calls += 1
            return [RawSearchResult(url="http://x", snippet="s", title="t")]

    client = DummyClient()
    first = cached_search("q", client)
    second = cached_search("q", client)
    assert first == second
    assert client.calls == 1

    async def hit_count() -> int:
        async with get_db_session() as conn:
            cur = await conn.execute(
                "SELECT hit_count FROM retrieval_cache WHERE query = ?",
                ("q",),
            )
            row = await cur.fetchone()
            await cur.close()
            return row[0]

    assert asyncio.run(hit_count()) == 1


def test_cached_search_falls_back_to_dense(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    async def init_db() -> None:
        async with get_db_session() as conn:
            await conn.execute(CREATE_CACHE_SQL)
            await conn.commit()

    asyncio.run(init_db())

    class FailingClient:
        def search(self, query: str):  # pragma: no cover - simple
            raise RuntimeError("boom")

    docs = [RawSearchResult(url="http://a", snippet="hello world", title="A")]
    dense = DenseRetriever(docs)
    results = cached_search("hello", FailingClient(), dense)
    assert results == docs
