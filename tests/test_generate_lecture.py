"""Tests for the lecture generation CLI."""

from __future__ import annotations

import asyncio
import sys
import types
from contextlib import asynccontextmanager


def test_generate(monkeypatch):
    """_generate returns final graph state."""

    async def fake_ainvoke(payload, config=None):  # type: ignore[unused-argument]
        assert payload["prompt"] == "topic"
        return {"title": "Test"}

    fake_graph = types.SimpleNamespace(ainvoke=fake_ainvoke)

    @asynccontextmanager
    async def fake_saver():
        yield object()

    monkeypatch.setitem(
        sys.modules,
        "core.orchestrator",
        types.SimpleNamespace(graph=fake_graph, create_checkpoint_saver=fake_saver),
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
