"""Tests for the lecture generation CLI."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import sys
import types


@dataclass
class DummyResult:
    """Minimal stand-in for :class:`agents.models.WeaveResult`."""

    title: str
    learning_objectives: list[str]
    activities: list
    duration_min: int


def test_generate(monkeypatch):
    """_generate returns a dictionary derived from the weave result."""

    async def fake_run_content_weaver(_state):
        return DummyResult("Test", [], [], 0)

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
