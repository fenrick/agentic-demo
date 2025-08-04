"""Content weaver node assembling draft material."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator, List

from jsonschema import Draft202012Validator

from core.state import State
from prompts import get_prompt

from .agent_wrapper import init_chat_model
from .models import (
    Activity,
    AssessmentItem,
    Citation,
    SlideBullet,
    WeaveResult,
)
from .streaming import stream_debug, stream_messages


class RetryableError(RuntimeError):
    """Signal that the operation can be retried."""


class SchemaError(RetryableError):
    """Raised when LLM output fails schema validation."""


_schema_cache: dict | None = None


def load_schema() -> dict:
    """Load the lecture schema from disk once."""
    global _schema_cache
    if _schema_cache is None:
        schema_path = (
            Path(__file__).resolve().parents[1] / "schemas" / "lecture_schema.json"
        )
        with schema_path.open("r", encoding="utf-8") as f:
            _schema_cache = json.load(f)
    return _schema_cache


@dataclass(slots=True)
class ValidationResult:
    """Outcome of schema validation."""

    valid: bool
    errors: List[str]


def validate_against_schema(payload: dict) -> ValidationResult:
    """Validate payload using the lecture schema."""
    schema = load_schema()
    validator = Draft202012Validator(schema)
    errors = [
        f"{'/'.join(str(p) for p in err.path)}: {err.message}"
        for err in validator.iter_errors(payload)
    ]
    return ValidationResult(valid=not errors, errors=errors)


def parse_function_response(tokens: List[str]) -> dict:
    """Assemble streamed ``tokens`` into a JSON object."""

    raw = "".join(tokens)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise RetryableError("model returned invalid JSON") from exc


async def call_openai_function(prompt: str, schema: dict) -> AsyncGenerator[str, None]:
    """Invoke an LLM via LangChain and yield streamed tokens."""

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
    except Exception:  # pragma: no cover - dependency not installed

        async def empty() -> AsyncGenerator[str, None]:
            if False:
                yield ""  # type: ignore

        return empty()

    model = init_chat_model(streaming=True)
    if model is None:

        async def empty() -> AsyncGenerator[str, None]:
            if False:
                yield ""  # type: ignore

        return empty()

    async def generator() -> AsyncGenerator[str, None]:
        messages = [
            SystemMessage(content=get_prompt("content_weaver_system")),
            HumanMessage(content=prompt),
        ]
        stream = model.astream(messages)
        if hasattr(stream, "__await__"):
            stream = await stream
        async for chunk in stream:  # pragma: no cover - streaming
            if chunk.content:
                yield chunk.content

    return generator()


async def content_weaver(state: State, section_id: int | None = None) -> WeaveResult:
    """Generate lecture content via an LLM and enforce schema compliance.

    Args:
        state: Current orchestration state providing the outline and prompt.
        section_id: Optional index into ``state.outline.steps`` specifying a
            particular section to generate. When omitted the full ``state.prompt``
            is used.
    """

    schema = load_schema()
    tokens: List[str] = []

    prompt = state.prompt
    if section_id is not None and state.outline:
        if section_id < 0 or section_id >= len(state.outline.steps):
            raise IndexError("section_id out of range")
        prompt = state.outline.steps[section_id]

    async for token in call_openai_function(prompt, schema):
        tokens.append(token)
        stream_messages(token)
    payload = parse_function_response(tokens)
    validation = validate_against_schema(payload)
    if not validation.valid:
        error_msg = "; ".join(validation.errors)
        stream_debug(error_msg)
        raise SchemaError(error_msg)
    activities = [Activity(**a) for a in payload.get("activities", [])]
    slide_bullets = (
        [SlideBullet(**b) for b in payload.get("slide_bullets", [])]
        if payload.get("slide_bullets")
        else None
    )
    assessment = (
        [AssessmentItem(**a) for a in payload.get("assessment", [])]
        if payload.get("assessment")
        else None
    )
    references = (
        [Citation(**c) for c in payload.get("references", [])]
        if payload.get("references")
        else None
    )
    return WeaveResult(
        title=payload.get("title", ""),
        learning_objectives=payload.get("learning_objectives", []),
        activities=activities,
        duration_min=payload.get("duration_min", 0),
        author=payload.get("author"),
        date=payload.get("date"),
        version=payload.get("version"),
        summary=payload.get("summary"),
        tags=payload.get("tags"),
        prerequisites=payload.get("prerequisites"),
        slide_bullets=slide_bullets,
        speaker_notes=payload.get("speaker_notes"),
        assessment=assessment,
        references=references,
    )


async def run_content_weaver(
    state: State, section_id: int | None = None
) -> WeaveResult:
    """Entry point used by the orchestrator.

    Args:
        state: Orchestrator state passed through the graph.
        section_id: Optional outline index to generate only a specific section.
    """

    return await content_weaver(state, section_id=section_id)
