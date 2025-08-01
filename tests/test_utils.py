import pytest

from app import utils


def test_load_prompt(tmp_path, monkeypatch):
    prom_dir = tmp_path / "prompts"
    prom_dir.mkdir()
    (prom_dir / "test.yaml").write_text("content: hi")
    monkeypatch.setattr(utils, "PROMPTS_PATH", prom_dir)
    assert utils.load_prompt("test") == "hi"

    with pytest.raises(FileNotFoundError):
        utils.load_prompt("missing")
