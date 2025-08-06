"""Helpers for parsing JSON from LLM outputs."""

from __future__ import annotations

import json
from typing import Any, Dict


def load_json(text: str) -> Dict[str, Any] | None:
    """Attempt to parse ``text`` as JSON.

    The function strips surrounding Markdown code fences and extracts the first
    JSON object found within the string. It returns ``None`` when parsing fails.
    """

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}") + 1
        if start >= 0 and end > start:
            snippet = text[start:end]
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                return None
        return None


__all__ = ["load_json"]
