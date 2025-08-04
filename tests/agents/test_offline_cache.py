import importlib

from agents.researcher_web import RawSearchResult
import agents.offline_cache as offline_cache


def test_cache_respects_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "key")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    module = importlib.reload(offline_cache)

    module.save_cached_results(
        "hello world", [RawSearchResult(url="http://a", snippet="b", title="c")]
    )

    expected_file = tmp_path / "cache" / "hello_world.json"
    assert module.CACHE_DIR == tmp_path / "cache"
    assert expected_file.exists()
