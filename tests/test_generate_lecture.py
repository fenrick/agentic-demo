"""Tests for the lecture generation CLI."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import sys
import types


@dataclass
class DummyModule:
    """Minimal stand-in for :class:`core.state.Module`."""

    id: str
    title: str
    duration_min: int
    learning_objectives: list[str]

    def model_dump(self):
        return {
            "id": self.id,
            "title": self.title,
            "duration_min": self.duration_min,
            "learning_objectives": self.learning_objectives,
        }


def test_generate(monkeypatch):
    """_generate returns a dictionary derived from the weave result."""

    async def fake_run_content_weaver(_state):
        return DummyModule("m1", "Test", 0, [])

    class DummyState:
        def __init__(self, prompt: str) -> None:
            self.prompt = prompt

    monkeypatch.setitem(
        sys.modules,
        "agents.content_weaver",
        types.SimpleNamespace(run_content_weaver=fake_run_content_weaver),
    )
    monkeypatch.setitem(
        sys.modules, "core.state", types.SimpleNamespace(State=DummyState)
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
