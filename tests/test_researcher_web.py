import asyncio
import time
import urllib.request
import importlib

import pytest

from web import CitationResult, researcher_web

web_module = importlib.import_module("web.researcher_web")


@pytest.mark.asyncio
async def test_researcher_web_deduplicates_and_fetches_concurrently():
    urls = [
        "https://Example.com/path",
        "http://example.com/path/",
        "https://another.com/article",
    ]
    call_count = 0

    async def fake_fetch(url: str) -> CitationResult:
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)
        return CitationResult(url=url, content=url.upper())

    start = time.perf_counter()
    results = await researcher_web(urls, fetch=fake_fetch)
    elapsed = time.perf_counter() - start

    assert call_count == len(urls)
    assert [r.url for r in results] == [urls[0], urls[2]]
    assert elapsed < 0.2


@pytest.mark.asyncio
async def test_researcher_web_skips_failures_and_normalizes_urls() -> None:
    urls = ["https://www.example.com/", "http://example.com"]

    async def fake_fetch(url: str) -> CitationResult:
        if "www" in url:
            raise RuntimeError("boom")
        return CitationResult(url=url, content="ok")

    results = await researcher_web(urls, fetch=fake_fetch)
    assert [r.url for r in results] == [urls[1]]


@pytest.mark.asyncio
async def test_fetch_uses_urlopen(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyResponse:
        def read(self) -> bytes:
            return b"data"

    class DummyContext:
        def __enter__(self) -> DummyResponse:  # pragma: no cover - simple
            return DummyResponse()

        def __exit__(self, *args) -> None:  # pragma: no cover - simple
            return None

    monkeypatch.setattr(urllib.request, "urlopen", lambda url: DummyContext())

    async def fake_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(web_module.asyncio, "to_thread", fake_to_thread)

    result = await web_module._fetch("http://example.com")
    assert result.content == "data"
