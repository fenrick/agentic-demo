"""Tests for the lecture generation CLI."""

from __future__ import annotations

import asyncio
import logging
import sys
import types

from cli.generate_lecture import save_markdown


def test_generate(monkeypatch):
    """_generate returns final graph state."""

    async def fake_run(state):  # type: ignore[unused-argument]
        state.title = "Test"

    fake_graph = types.SimpleNamespace(run=fake_run)

    monkeypatch.setitem(
        sys.modules,
        "core.orchestrator",
        types.SimpleNamespace(graph=fake_graph),
    )

    from cli.generate_lecture import _generate

    result = asyncio.run(_generate("topic"))
    assert result["title"] == "Test"


def test_generate_verbose_streams_progress(monkeypatch, caplog):
    """_generate streams progress messages when verbose."""

    async def fake_stream(state):  # type: ignore[unused-argument]
        logging.getLogger("core.orchestrator").info("progress for %s", state.prompt)
        yield {"type": "action", "payload": "X"}

    fake_graph = types.SimpleNamespace(stream=fake_stream)

    monkeypatch.setitem(
        sys.modules,
        "core.orchestrator",
        types.SimpleNamespace(graph=fake_graph),
    )

    from cli.generate_lecture import _generate

    with caplog.at_level(logging.INFO):
        asyncio.run(_generate("topic", verbose=True))

    assert "progress for topic" in caplog.text


def test_parse_args_verbose(monkeypatch):
    """parse_args recognizes the --verbose flag."""

    from cli.generate_lecture import parse_args

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "topic",
            "--verbose",
            "--portfolio",
            "STEM",
            "--portfolio",
            "Education",
        ],
    )
    args = parse_args()
    assert args.verbose is True
    assert args.topic == "topic"
    assert args.output.name == "run_output.md"
    assert args.portfolios == ["STEM", "Education"]


def test_main_writes_output(monkeypatch, tmp_path):
    """main writes the lecture payload to the specified markdown file."""
    fake_streaming = types.ModuleType("agents.streaming")
    fake_streaming.stream_messages = lambda *_a, **_k: None
    sys.modules["agents.streaming"] = fake_streaming

    fake_observability = types.ModuleType("observability")
    fake_observability.init_observability = lambda: None
    fake_observability.install_auto_tracing = lambda: None
    sys.modules["observability"] = fake_observability

    async def fake_generate(topic: str, verbose: bool = False) -> dict[str, str]:
        return {"result": topic}

    def fake_parse_args() -> types.SimpleNamespace:
        return types.SimpleNamespace(
            topic="demo",
            verbose=False,
            output=tmp_path / "out.md",
            portfolios=["Research & Innovation"],
        )

    from cli import generate_lecture

    monkeypatch.setattr(generate_lecture, "_generate", fake_generate)
    monkeypatch.setattr(generate_lecture, "parse_args", fake_parse_args)

    from cli.generate_lecture import slugify

    generate_lecture.main()
    out_file = tmp_path / f"out_{slugify('Research & Innovation')}.md"
    content = out_file.read_text()
    assert "demo" in content


def test_save_markdown_formats_lecture(tmp_path):
    """save_markdown renders structured lecture Markdown when modules exist."""
    payload = {
        "modules": [
            {
                "id": "m1",
                "title": "Demo",
                "duration_min": 10,
                "learning_objectives": ["lo1"],
            }
        ]
    }
    out = tmp_path / "lecture.md"
    save_markdown(out, "Demo", payload)
    text = out.read_text()
    assert "## Learning Objectives" in text
    assert "- lo1" in text
