"""Tests for core :mod:`core.state` dataclass implementation."""

from dataclasses import is_dataclass

from core.state import ActionLog, Citation, Outline, State
from pydantic import TypeAdapter


def test_state_defaults() -> None:
    """State should expose dataclass structure with expected defaults."""
    state = State()
    assert is_dataclass(state)
    assert state.prompt == ""
    assert state.sources == []
    assert state.outline is None
    assert state.log == []
    assert state.version == 1


def test_json_round_trip() -> None:
    """State should serialize and deserialize via JSON consistently."""
    citation = Citation(url="https://example.com")
    outline = Outline(steps=["intro"])
    log_entry = ActionLog(message="start")
    state = State(
        prompt="p",
        sources=[citation],
        outline=outline,
        log=[log_entry],
        version=2,
    )
    adapter = TypeAdapter(State)
    json_data = adapter.dump_json(state)
    assert isinstance(json_data, (bytes, bytearray))
    new_state = adapter.validate_json(json_data)
    assert new_state == state
