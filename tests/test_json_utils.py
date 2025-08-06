"""Tests for JSON parsing helpers."""

from __future__ import annotations

from agents.json_utils import load_json


def test_load_json_parses_plain_json() -> None:
    """load_json returns a dict for simple JSON strings."""
    assert load_json('{"a": 1}') == {"a": 1}


def test_load_json_extracts_fenced_json() -> None:
    """load_json handles JSON wrapped in Markdown fences."""
    text = 'Here is data:\n```json\n{"b": 2}\n```'
    assert load_json(text) == {"b": 2}
