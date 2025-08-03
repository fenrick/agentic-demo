"""Content weaver node assembling draft material."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

from jsonschema import Draft202012Validator

from core.state import State
from .models import WeaveResult

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


async def run_content_weaver(state: State) -> WeaveResult:
    """Call LLM, apply schema, and stream back outline tokens.

    TODO: Integrate actual LLM calls and streaming mechanisms.
    """
    return WeaveResult(learning_objectives=[], activities=[], duration_min=0)
