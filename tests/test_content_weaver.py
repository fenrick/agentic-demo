"""Tests for content weaver helpers."""

from __future__ import annotations

import asyncio
import json
import sys
import types
from typing import Any

import pytest
from pydantic import ValidationError

from agents import content_weaver
from agents.content_weaver import RetryableError, WeaveResult


def test_call_openai_function_supplies_schema(monkeypatch: Any) -> None:
    """call_openai_function sends the model JSON schema."""

    captured: dict[str, Any] = {}

    class DummyAgent:
        def __init__(self, *, instructions: list[str], model: Any) -> None:
            captured["instructions"] = instructions

        def run_stream(self, prompt: str) -> Any:  # pragma: no cover - used in test
            class Resp:
                async def __aenter__(self) -> "Resp":
                    return self

                async def __aexit__(self, *args: Any) -> None:
                    return None

                def stream_text(self, delta: bool = False) -> Any:
                    async def gen() -> Any:
                        yield ""

                    return gen()

            return Resp()

    monkeypatch.setitem(
        sys.modules, "pydantic_ai", types.SimpleNamespace(Agent=DummyAgent)
    )

    monkeypatch.setitem(
        sys.modules,
        "agents.agent_wrapper",
        types.SimpleNamespace(
            init_chat_model=lambda **_: types.SimpleNamespace(_model=None)
        ),
    )

    schema_marker = {"marker": "value"}
    monkeypatch.setattr(
        WeaveResult, "model_json_schema", staticmethod(lambda: schema_marker)
    )

    async def run() -> None:
        stream = await content_weaver.call_openai_function("topic")
        _ = [token async for token in stream]

    asyncio.run(run())

    schema_str = json.dumps(schema_marker, indent=2)
    instructions = captured.get("instructions", [])
    assert any(schema_str in instr for instr in instructions)


def test_content_weaver_propagates_validation_error(monkeypatch: Any) -> None:
    """Invalid model output raises :class:`RetryableError`."""

    async def fake_call(prompt: str) -> Any:  # pragma: no cover - used in test
        async def gen() -> Any:
            yield "{}"  # missing required fields

        return gen()

    monkeypatch.setattr(content_weaver, "call_openai_function", fake_call)

    from core.state import State

    state = State(prompt="topic")
    with pytest.raises(RetryableError):
        asyncio.run(content_weaver.content_weaver(state))


def test_weave_result_requires_all_fields() -> None:
    """The :class:`WeaveResult` model enforces required fields."""

    with pytest.raises(ValidationError):
        WeaveResult.model_validate({})


def test_call_openai_function_emits_logfire_trace(monkeypatch: Any) -> None:
    """``call_openai_function`` should emit a logfire trace via the agent."""

    trace_calls: list[str] = []

    class LogfireStub:
        def trace(self, name: str, *_a, **_k):  # pragma: no cover - simple stub
            trace_calls.append(name)

            class _Span:
                async def __aenter__(self):
                    return None

                async def __aexit__(self, *exc):
                    pass

            return _Span()

    monkeypatch.setitem(sys.modules, "logfire", LogfireStub())

    class DummyAgent:
        def __init__(self, *, instructions: list[str], model: Any) -> None:
            pass

        def run_stream(self, prompt: str) -> Any:  # pragma: no cover - used in test
            import logfire

            span: Any = logfire.trace("agent")

            class Resp:
                async def __aenter__(self) -> "Resp":
                    await span.__aenter__()
                    return self

                async def __aexit__(self, *args: Any) -> None:
                    await span.__aexit__(*args)

                def stream_text(self, delta: bool = False) -> Any:
                    async def gen() -> Any:
                        yield ""

                    return gen()

            return Resp()

    monkeypatch.setitem(
        sys.modules, "pydantic_ai", types.SimpleNamespace(Agent=DummyAgent)
    )
    monkeypatch.setitem(
        sys.modules,
        "agents.agent_wrapper",
        types.SimpleNamespace(
            init_chat_model=lambda **_: types.SimpleNamespace(_model=None)
        ),
    )

    async def run() -> None:
        stream = await content_weaver.call_openai_function("topic")
        _ = [token async for token in stream]

    asyncio.run(run())
    assert "agent" in trace_calls
