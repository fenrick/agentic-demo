import sys
import types

import config

pkg = types.ModuleType("agentic_demo")
pkg.config = config
sys.modules["agentic_demo"] = pkg
sys.modules["agentic_demo.config"] = config

from agents.researcher_web import CitationDraft, RawSearchResult
from agents.researcher_web_runner import run_web_search
from core.state import State


def _set_env(monkeypatch, offline: bool, provider: str = "perplexity") -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "pp")
    monkeypatch.setenv("TAVILY_API_KEY", "tv")
    monkeypatch.setenv("MODEL_NAME", "gpt")
    monkeypatch.setenv("DATA_DIR", "/tmp")
    monkeypatch.setenv("OFFLINE_MODE", "1" if offline else "0")
    monkeypatch.setenv("SEARCH_PROVIDER", provider)


def test_run_web_search_online(monkeypatch):
    _set_env(monkeypatch, offline=False, provider="perplexity")

    state = State(prompt="cats")
    called = {"search": False, "fallback": False}
    results = [RawSearchResult(url="u", snippet="s", title="t")]

    def fake_search(self, query):
        called["search"] = True
        return results

    def fake_fallback(self, query):
        called["fallback"] = True
        return []

    monkeypatch.setattr(
        "agents.researcher_web.PerplexityClient.search", fake_search, raising=False
    )
    monkeypatch.setattr(
        "agents.researcher_web.PerplexityClient.fallback_search",
        fake_fallback,
        raising=False,
    )

    citations = run_web_search(state)
    assert called["search"] is True
    assert called["fallback"] is False
    assert citations == [CitationDraft(url="u", snippet="s", title="t")]


def test_run_web_search_offline(monkeypatch):
    _set_env(monkeypatch, offline=True)

    state = State(prompt="dogs")
    called = {"search": False}
    results = [RawSearchResult(url="u2", snippet="s2", title="t2")]

    def fake_search(self, query):
        called["search"] = True
        return results

    monkeypatch.setattr(
        "agents.cache_backed_researcher.CacheBackedResearcher.search",
        fake_search,
        raising=False,
    )

    citations = run_web_search(state)
    assert called["search"] is True
    assert citations == [CitationDraft(url="u2", snippet="s2", title="t2")]


def test_run_web_search_tavily(monkeypatch):
    _set_env(monkeypatch, offline=False, provider="tavily")

    state = State(prompt="birds")
    called = {"search": False}
    results = [RawSearchResult(url="u3", snippet="s3", title="t3")]

    class Dummy:
        def __init__(self, api_key: str):
            pass

        def search(self, query):
            called["search"] = True
            return results

    monkeypatch.setattr("agents.researcher_web_runner.TavilyClient", Dummy)

    citations = run_web_search(state)
    assert called["search"] is True
    assert citations == [CitationDraft(url="u3", snippet="s3", title="t3")]
