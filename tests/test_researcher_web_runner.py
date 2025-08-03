from agents.researcher_web import RawSearchResult
from agents.researcher_web_runner import CitationDraft, run_web_search
from core.state import State


def _set_env(monkeypatch, offline: bool) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "pp")
    monkeypatch.setenv("MODEL_NAME", "gpt")
    monkeypatch.setenv("DATA_DIR", "/tmp")
    monkeypatch.setenv("OFFLINE_MODE", "1" if offline else "0")


def test_run_web_search_online(monkeypatch):
    _set_env(monkeypatch, offline=False)

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
    called = {"search": False, "fallback": False}
    results = [RawSearchResult(url="u2", snippet="s2", title="t2")]

    def fake_search(self, query):
        called["search"] = True
        return []

    def fake_fallback(self, query):
        called["fallback"] = True
        return results

    monkeypatch.setattr(
        "agents.researcher_web.PerplexityClient.search", fake_search, raising=False
    )
    monkeypatch.setattr(
        "agents.researcher_web.PerplexityClient.fallback_search",
        fake_fallback,
        raising=False,
    )

    citations = run_web_search(state)
    assert called["search"] is False
    assert called["fallback"] is True
    assert citations == [CitationDraft(url="u2", snippet="s2", title="t2")]
