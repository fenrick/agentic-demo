from agents.copyright_filter import filter_allowlist
from agents.researcher_web import CitationDraft, rank_by_authority


def _set_env(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "sk")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "pk")
    monkeypatch.setenv("MODEL_NAME", "gpt")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))


def test_rank_by_authority_sorts(monkeypatch, tmp_path):
    _set_env(monkeypatch, tmp_path)
    low = CitationDraft(url="http://blog.com", snippet="", title="")
    high = CitationDraft(url="http://uni.edu", snippet="", title="")
    ranked = rank_by_authority([low, high])
    assert ranked[0] == high


def test_filter_allowlist(monkeypatch, tmp_path):
    _set_env(monkeypatch, tmp_path)
    monkeypatch.setenv("ALLOWLIST_DOMAINS", '["example.com", ".edu"]')
    drafts = [
        CitationDraft(url="http://example.com/a", snippet="", title=""),
        CitationDraft(url="http://other.net", snippet="", title=""),
        CitationDraft(url="http://site.edu/info", snippet="", title=""),
    ]
    kept, dropped = filter_allowlist(drafts)
    assert [d.url for d in kept] == ["http://example.com/a", "http://site.edu/info"]
    assert [d.url for d in dropped] == ["http://other.net"]
