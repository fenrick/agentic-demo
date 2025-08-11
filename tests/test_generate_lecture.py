"""Tests for the lecture generation CLI."""

from __future__ import annotations

import asyncio
import sys
import types


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


def test_parse_args_verbose(monkeypatch):
    """parse_args recognizes the --verbose flag."""

    from cli.generate_lecture import parse_args

    monkeypatch.setattr(sys, "argv", ["prog", "topic", "--verbose"])
    args = parse_args()
    assert args.verbose is True
    assert args.topic == "topic"
    assert args.output.name == "run_output.md"


def test_main_writes_output(monkeypatch, tmp_path):
    """main writes the lecture payload to the specified markdown file."""
    fake_streaming = types.ModuleType("agents.streaming")
    fake_streaming.stream_messages = lambda *_a, **_k: None
    sys.modules["agents.streaming"] = fake_streaming

    fake_observability = types.ModuleType("observability")
    fake_observability.init_observability = lambda: None
    fake_observability.install_auto_tracing = lambda: None
    sys.modules["observability"] = fake_observability

    async def fake_generate(topic: str) -> dict[str, str]:
        return {"result": topic}

    def fake_parse_args() -> types.SimpleNamespace:
        return types.SimpleNamespace(
            topic="demo", verbose=False, output=tmp_path / "out.md"
        )

    from cli import generate_lecture

    monkeypatch.setattr(generate_lecture, "_generate", fake_generate)
    monkeypatch.setattr(generate_lecture, "parse_args", fake_parse_args)

    generate_lecture.main()
    content = (tmp_path / "out.md").read_text()
    assert "demo" in content
