"""Tests for content weaver helpers."""

from __future__ import annotations

import json
import sys
import types
from typing import Any

import pytest

from agents import content_weaver
from agents.content_weaver import parse_function_response, RetryableError


def test_parse_function_response_extracts_json() -> None:
    """parse_function_response returns the inner JSON block."""
    tokens = ["prefix", '{"title": "Demo"}', "suffix"]
    result = parse_function_response(tokens)
    assert result["title"] == "Demo"


def test_parse_function_response_errors_without_json() -> None:
    """parse_function_response raises when JSON is absent."""
    with pytest.raises(RetryableError):
        parse_function_response(["no json here"])


def test_call_openai_function_supplies_schema(monkeypatch: Any) -> None:
    """call_openai_function sends the lecture schema to the model."""

    class FakeMessage:
        def __init__(self, content: str) -> None:
            self.content = content

    fake_messages = types.SimpleNamespace(
        HumanMessage=FakeMessage, SystemMessage=FakeMessage
    )
    monkeypatch.setitem(sys.modules, "langchain_core.messages", fake_messages)

    captured: dict[str, Any] = {}

    class DummyModel:
        async def astream(self, messages: list[FakeMessage]) -> Any:
            captured["messages"] = messages

            async def gen() -> Any:
                yield FakeMessage("")

            return gen()

    def fake_init_chat_model(streaming: bool = True) -> DummyModel:
        return DummyModel()

    fake_wrapper = types.SimpleNamespace(init_chat_model=fake_init_chat_model)
    monkeypatch.setitem(sys.modules, "agents.agent_wrapper", fake_wrapper)

    schema_marker = {"marker": "value"}
    monkeypatch.setattr(content_weaver, "load_schema", lambda: schema_marker)

    async def run() -> None:
        stream = await content_weaver.call_openai_function("topic")
        _ = [token async for token in stream]

    import asyncio

    asyncio.run(run())

    schema_str = json.dumps(schema_marker, indent=2)
    messages = captured.get("messages", [])
    assert any(schema_str in m.content for m in messages)
