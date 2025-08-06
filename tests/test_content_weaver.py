"""Tests for content weaver helpers."""

from __future__ import annotations

import pytest

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
