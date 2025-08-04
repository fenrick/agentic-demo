import asyncio
import json

from agents import content_weaver as cw
from core.state import Outline, State


def test_call_openai_function_streams_tokens(monkeypatch):
    class FakeChunk:
        def __init__(self, content: str):
            self.content = content

    class FakeLLM:
        async def astream(self, *args, **kwargs):
            async def gen():
                yield FakeChunk("foo")
                yield FakeChunk("bar")

            return gen()

    monkeypatch.setattr(cw, "init_chat_model", lambda **_kwargs: FakeLLM())

    async def run_test():
        gen = await cw.call_openai_function("prompt", {})
        tokens: list[str] = []
        async for token in gen:
            tokens.append(token)
        return tokens

    assert asyncio.run(run_test()) == ["foo", "bar"]


def test_parse_and_validate_success(monkeypatch):
    async def fake_call_openai_function(prompt: str, schema: dict):
        yield json.dumps(
            {
                "title": "Sample",
                "learning_objectives": ["Understand"],
                "activities": [
                    {"type": "Lecture", "description": "Intro", "duration_min": 5}
                ],
                "duration_min": 5,
            }
        )

    monkeypatch.setattr(cw, "call_openai_function", fake_call_openai_function)
    monkeypatch.setattr(cw, "stream_messages", lambda token: None)

    async def run_test():
        state = State(prompt="topic")
        return await cw.content_weaver(state)

    state_result = asyncio.run(run_test())
    assert state_result.title == "Sample"
    assert state_result.activities[0].type == "Lecture"


def test_section_specific_prompt(monkeypatch):
    captured: list[str] = []

    async def fake_call_openai_function(prompt: str, schema: dict):
        captured.append(prompt)
        yield json.dumps(
            {
                "title": "Sec",
                "learning_objectives": [],
                "activities": [],
                "duration_min": 0,
            }
        )

    monkeypatch.setattr(cw, "call_openai_function", fake_call_openai_function)
    monkeypatch.setattr(cw, "stream_messages", lambda token: None)

    async def run_test():
        outline = Outline(steps=["first", "second"])
        state = State(prompt="topic", outline=outline)
        return await cw.content_weaver(state, section_id=1)

    asyncio.run(run_test())
    assert captured == ["second"]


def test_schema_validation_fails_and_raises(monkeypatch):
    async def fake_call_openai_function(prompt: str, schema: dict):
        yield json.dumps(
            {
                "learning_objectives": ["Objective"],
                "activities": [
                    {"type": "Lecture", "description": "Intro", "duration_min": 5}
                ],
                "duration_min": 5,
            }
        )

    monkeypatch.setattr(cw, "call_openai_function", fake_call_openai_function)
    monkeypatch.setattr(cw, "stream_messages", lambda token: None)
    monkeypatch.setattr(cw, "stream_debug", lambda message: None)

    async def run_test():
        state = State(prompt="topic")
        await cw.content_weaver(state)

    import pytest

    with pytest.raises(cw.SchemaError):
        asyncio.run(run_test())
