"""Tests for orchestration state model."""

from agentic_demo.orchestration.state import State


def test_state_defaults():
    """State should provide sensible default values."""
    state = State()
    assert state.prompt == ""
    assert state.sources == []
    assert state.outline == []
    assert state.log == []
    assert state.version == 1


def test_state_custom_values():
    """State should accept custom initialization values."""
    state = State(
        prompt="hi",
        sources=["doc"],
        outline=["step"],
        log=["msg"],
        version=2,
    )
    assert state.prompt == "hi"
    assert state.sources == ["doc"]
    assert state.outline == ["step"]
    assert state.log == ["msg"]
    assert state.version == 2
