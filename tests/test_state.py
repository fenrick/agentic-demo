"""Tests for core State model."""

from core.state import ActionLog, Citation, Outline, State


def test_state_defaults():
    """State should provide expected default values."""
    state = State()
    assert state.prompt == ""
    assert state.sources == []
    assert state.outline is None
    assert state.log == []
    assert state.version == 1


def test_json_round_trip():
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
    json_data = state.model_dump_json()
    assert isinstance(json_data, str)
    new_state = State.model_validate_json(json_data)
    assert new_state == state
