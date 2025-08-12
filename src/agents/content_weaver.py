"""Content weaver node assembling draft material."""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator, Sequence

from pydantic import ValidationError

from core.state import Citation, Module, State
from prompts import get_prompt

from .models import WeaveResult
from .streaming import stream_debug, stream_messages


class RetryableError(RuntimeError):
    """Signal that the operation can be retried."""


async def call_openai_function(
    prompt: str, sources: Sequence[Citation] | None = None
) -> AsyncGenerator[str, None]:
    """Invoke an LLM via Pydantic AI and yield streamed tokens.

    Args:
        prompt: Prompt passed to the agent.
        sources: Optional citation metadata to provide additional context.
    """

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
    instructions: list[str] = []
    if sources:
        lines = []
        for src in sources:
            if src.title and src.licence and src.retrieved_at:
                lines.append(
                    f"- {src.title} ({src.url}) – {src.licence} retrieved"
                    f" {src.retrieved_at}"
                )
        if lines:
            context = "\n".join(lines)
            instructions.append(
                "Use only the following sources. If a claim is not supported here, "
                "write it cautiously and avoid definitive language.\n"
                + context
            )
    instructions.extend(
        [
            get_prompt("content_weaver_system"),
            "Ensure the total duration equals the sum of activity durations.",
            f"Output must conform to this JSON schema:\n{schema}",
        ]
    )
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

    prompt = state.prompt
    if section_id is not None and state.outline:
        if section_id < 0 or section_id >= len(state.outline.steps):
            raise IndexError("section_id out of range")
        prompt = state.outline.steps[section_id]

    base_prompt = prompt
    error = "validation failed"
    for attempt in range(2):
        tokens: list[str] = []
        stream = await call_openai_function(prompt, state.sources)
        async for token in stream:
            tokens.append(token)
            stream_messages(token)
        raw = "".join(tokens)
        try:
            weave = WeaveResult.model_validate_json(raw)
        except ValidationError as exc:  # pragma: no cover - defensive
            stream_debug(str(exc))
            raise RetryableError("model returned invalid schema") from exc

        # Guardrail: ensure speaker notes provide sufficient material
        word_count = len(weave.speaker_notes.split()) if weave.speaker_notes else 0
        if word_count < 1200:
            prompt = (
                f"{base_prompt}\n"
                "Expand speaker_notes to 1500–2500 words with slide-scoped sections; "
                "keep JSON identical otherwise."
            )
            error = "speaker notes too short"
            continue

        # Guardrail: verify activity timings sum to declared duration
        total = sum(act.duration_min for act in weave.activities)
        if total != weave.duration_min:
            prompt = (
                f"{base_prompt}\n"
                "Fix timing so sum equals duration_min; keep content unchanged."
            )
            error = "duration mismatch"
            continue

        return weave

    raise RetryableError(f"{error} after retry")


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
        activities=weave.activities,
    )
    state.modules.append(module)
    return module
