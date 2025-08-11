"""Tests for state serialization edge cases."""

from __future__ import annotations

from core.state import ActionLog, State


def test_to_dict_serializes_datetimes() -> None:
    """State.to_dict serializes datetimes to strings."""
    state = State(prompt="topic")
    state.log.append(ActionLog(message="done"))
    data = state.to_dict()
    assert isinstance(data["log"][0]["timestamp"], str)
