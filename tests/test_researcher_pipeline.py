import os

import httpx
import pytest

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("PERPLEXITY_API_KEY", "test")

from agents.researcher_pipeline import CitationDraft, researcher_pipeline
from core.state import State


@pytest.mark.asyncio
async def test_pipeline_handles_web_search_error(monkeypatch):
    def fail_search(_state):
        raise httpx.HTTPError("search failure")

    monkeypatch.setattr("agents.researcher_pipeline.run_web_search", fail_search)
    state = State(prompt="topic")
    citations = await researcher_pipeline("query", state)
    assert citations == []


@pytest.mark.asyncio
async def test_pipeline_continues_on_license_and_db_errors(monkeypatch):
    drafts = [
        CitationDraft(url="https://example.edu/a", snippet="", title="A"),
        CitationDraft(url="https://example.edu/b", snippet="", title="B"),
    ]

    def good_search(_state):
        return drafts

    async def flaky_lookup(url: str) -> str:
        if url.endswith("/b"):
            raise httpx.HTTPError("network issue")
        return "MIT"

    async def flaky_insert(self, citation):
        if str(citation.url).endswith("/b"):
            raise RuntimeError("db down")
        return None

    monkeypatch.setattr("agents.researcher_pipeline.run_web_search", good_search)
    monkeypatch.setattr("agents.researcher_pipeline._lookup_licence", flaky_lookup)
    monkeypatch.setattr("agents.researcher_pipeline.CitationRepo.insert", flaky_insert)

    state = State(prompt="topic")
    citations = await researcher_pipeline("query", state)
    assert len(citations) == 1
    assert str(citations[0].url) == "https://example.edu/a"
    assert citations[0].licence == "MIT"
