from pathlib import Path

from prompts import get_prompt, load_prompts


def test_get_prompt_caches_file_reads(monkeypatch):
    """Prompt file should only be read once due to caching."""

    calls = {"count": 0}
    original_open = Path.open

    def counting_open(self, *args, **kwargs):
        calls["count"] += 1
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", counting_open)
    load_prompts.cache_clear()

    first = get_prompt("content_weaver_system")
    second = get_prompt("content_weaver_system")

    assert first == second
    assert calls["count"] == 1
