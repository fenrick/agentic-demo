"""Content weaver node assembling draft material."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator, List

from jsonschema import Draft202012Validator

from core.state import State

from .agent_wrapper import get_llm_params
from .models import (Activity, AssessmentItem, Citation, SlideBullet,
                     WeaveResult)


class RetryableError(RuntimeError):
    """Signal that the operation can be retried."""


class SchemaError(RetryableError):
    """Raised when LLM output fails schema validation."""


def stream_messages(token: str) -> None:
    """Forward ``token`` over the LangGraph "messages" channel."""

    try:
        from langgraph_sdk import stream  # type: ignore

        stream("messages", token)
    except Exception:  # pragma: no cover - optional dependency
        print(token, end="", flush=True)


def stream_debug(message: str) -> None:
    """Forward ``message`` over the LangGraph "debug" channel."""

    try:
        from langgraph_sdk import stream  # type: ignore

        stream("debug", message)
    except Exception:  # pragma: no cover - optional dependency
        print(message, flush=True)


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
    """Invoke OpenAI with ``schema`` and yield streamed tokens."""

    try:
        from openai import AsyncOpenAI  # type: ignore
    except Exception:  # pragma: no cover - dependency not installed

        async def empty() -> AsyncGenerator[str, None]:
            if False:
                yield ""  # type: ignore

        return empty()

    client = AsyncOpenAI()

    async def generator() -> AsyncGenerator[str, None]:
        response = await client.responses.stream(
            **get_llm_params(),
            messages=[
                {
                    "role": "system",
                    "content": "You are an academic content weaver producing lectures.",
                },
                {"role": "user", "content": prompt},
            ],
            tools=[
                {
                    "type": "function",
                    "function": {"name": "weave", "parameters": schema},
                }
            ],
        )
        async for event in response:  # pragma: no cover - streaming is side effect
            if event.type == "response.output_text.delta":
                yield event.delta

    return generator()


async def content_weaver(state: State) -> WeaveResult:
    """Generate lecture content via an LLM and enforce schema compliance."""

    schema = load_schema()
    tokens: List[str] = []
    async for token in call_openai_function(state.prompt, schema):
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


async def run_content_weaver(state: State) -> WeaveResult:
    """Entry point used by the orchestrator."""

    return await content_weaver(state)
