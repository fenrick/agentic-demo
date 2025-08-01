import pytest
import pathlib

from app import utils


def test_load_prompt(tmp_path, monkeypatch):
    prom_dir = tmp_path / "prompts"
    prom_dir.mkdir()
    (prom_dir / "test.yaml").write_text("content: hi")
    monkeypatch.setattr(utils, "PROMPTS_PATH", prom_dir)
    assert utils.load_prompt("test") == "hi"

    with pytest.raises(FileNotFoundError):
        utils.load_prompt("missing")


def test_load_prompt_with_prompt_key(tmp_path, monkeypatch):
    prom_dir = tmp_path / "prompts"
    prom_dir.mkdir()
    (prom_dir / "new.yaml").write_text("prompt: hi")
    monkeypatch.setattr(utils, "PROMPTS_PATH", prom_dir)
    assert utils.load_prompt("new") == "hi"


def test_safe_load_without_yaml(monkeypatch):
    text = "prompt: |\n  hello\n  there"
    monkeypatch.setattr(utils, "yaml", None)
    data = utils._safe_load(text)
    assert data == {"prompt": "hello\nthere"}


def test_repository_prompts_load(monkeypatch):
    monkeypatch.setattr(utils, "PROMPTS_PATH", pathlib.Path("app/prompts"))
    assert utils.load_prompt("plan").startswith("You are an expert planner")
    assert utils.load_prompt("research").startswith("Gather concise background")
    assert utils.load_prompt("draft").startswith("Compose a brief")
    assert utils.load_prompt("review").startswith("Review the text below")
    assert utils.load_prompt("overlay").startswith("Seamlessly integrate")


def test_load_tools(tmp_path, monkeypatch):
    prom_dir = tmp_path / "prompts"
    prom_dir.mkdir()
    tools_yaml = prom_dir / "tools.yaml"
    tools_yaml.write_text(
        """
tools:
  search:
    description: search tool
    agents: [research]
"""
    )
    monkeypatch.setattr(utils, "PROMPTS_PATH", prom_dir)
    data = utils.load_tools()
    assert data["search"]["description"] == "search tool"
    assert "research" in data["search"]["agents"]
