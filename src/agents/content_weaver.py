"""Content weaver node assembling draft material."""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

from pydantic import ValidationError

from core.state import Module, State
from prompts import get_prompt

from .models import WeaveResult
from .streaming import stream_debug, stream_messages


class RetryableError(RuntimeError):
    """Signal that the operation can be retried."""


async def call_openai_function(prompt: str) -> AsyncGenerator[str, None]:
    """Invoke an LLM via Pydantic AI and yield streamed tokens."""

    try:
        from pydantic_ai import Agent
        from .model_utils import init_model
    except Exception:  # pragma: no cover - dependency not installed
        logging.exception("Content weaver dependencies unavailable")

        async def empty() -> AsyncGenerator[str, None]:
            if False:
                yield ""  # type: ignore[misc]

        return empty()

    model = init_model()
    if model is None:

        async def empty() -> AsyncGenerator[str, None]:
            if False:
                yield ""  # type: ignore[misc]

        return empty()

    schema = json.dumps(WeaveResult.model_json_schema(), indent=2)
    instructions = [
        get_prompt("content_weaver_system"),
        f"Output must conform to this JSON schema:\n{schema}",
    ]
    agent = Agent(model=model, instructions=instructions)

    async def generator() -> AsyncGenerator[str, None]:
        async with agent.run_stream(prompt) as response:  # pragma: no cover - streaming
            async for chunk in response.stream_text(delta=True):
                if chunk:
                    yield chunk

    return generator()


async def content_weaver(state: State, section_id: int | None = None) -> WeaveResult:
    """Generate lecture content via an LLM and enforce schema compliance.

    Args:
        state: Current orchestration state providing the outline and prompt.
        section_id: Optional index into ``state.outline.steps`` specifying a
            particular section to generate. When omitted the full ``state.prompt``
            is used.
    """

    tokens: list[str] = []

    prompt = state.prompt
    if section_id is not None and state.outline:
        if section_id < 0 or section_id >= len(state.outline.steps):
            raise IndexError("section_id out of range")
        prompt = state.outline.steps[section_id]

    stream = await call_openai_function(prompt)
    async for token in stream:
        tokens.append(token)
        stream_messages(token)
    raw = "".join(tokens)
    try:
        return WeaveResult.model_validate_json(raw)
    except ValidationError as exc:  # pragma: no cover - defensive
        stream_debug(str(exc))
        raise RetryableError("model returned invalid schema") from exc


async def run_content_weaver(state: State, section_id: int | None = None) -> Module:
    """Generate content and store it in ``state.modules``.

    Args:
        state: Orchestrator state passed through the graph.
        section_id: Optional outline index to generate only a specific section.

    Returns:
        Module: Simplified representation of the generated content for
        downstream policies.
    """

    weave = await content_weaver(state, section_id=section_id)
    module = Module(
        id=f"m{len(state.modules) + 1}",
        title=weave.title,
        duration_min=weave.duration_min,
        learning_objectives=weave.learning_objectives,
    )
    state.modules.append(module)
    return module
