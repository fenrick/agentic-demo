"""Tests for core :mod:`core.state` dataclass implementation."""

from dataclasses import is_dataclass

import pytest
from pydantic import TypeAdapter

from core.state import (
    ActionLog,
    Citation,
    Outline,
    State,
    Module,
    CritiqueReport,
    FactCheckReport,
    increment_version,
    validate_state,
)


@pytest.fixture()
def sample_state() -> State:
    """Provide a populated :class:`State` instance for reuse."""
    citation = Citation(url="https://example.com")
    module = Module(
        id="m1",
        title="Intro",
        duration_min=5,
        learning_objectives=["Understand"],
    )
    outline = Outline(
        steps=["intro"], learning_objectives=["Understand"], modules=[module]
    )
    log_entry = ActionLog(message="start")
    return State(
        prompt="p",
        sources=[citation],
        outline=outline,
        log=[log_entry],
        learning_objectives=["Understand"],
        modules=[module],
        critique_report=CritiqueReport(notes=["looks good"]),
        factcheck_report=FactCheckReport(issues=[]),
        version=2,
    )


def test_state_defaults() -> None:
    """State should expose dataclass structure with expected defaults."""
    state = State()
    assert is_dataclass(state)
    assert state.prompt == ""
    assert state.sources == []
    assert state.outline is None
    assert state.log == []
    assert state.retries == {}
    assert state.learning_objectives == []
    assert state.modules == []
    assert state.critique_report is None
    assert state.factcheck_report is None
    assert state.version == 1


def test_json_round_trip(sample_state: State) -> None:
    """State should serialize and deserialize via JSON consistently."""
    adapter = TypeAdapter(State)
    json_data = adapter.dump_json(sample_state)
    assert isinstance(json_data, (bytes, bytearray))
    new_state = adapter.validate_json(json_data)
    assert new_state == sample_state


def test_dict_round_trip(sample_state: State) -> None:
    """``to_dict`` and ``from_dict`` should round-trip the data losslessly."""
    raw = sample_state.to_dict()
    assert isinstance(raw, dict)
    rebuilt = State.from_dict(raw)
    assert rebuilt == sample_state


def test_increment_version(sample_state: State) -> None:
    """``increment_version`` should mutate and return the incremented value."""
    original = sample_state.version
    new_version = increment_version(sample_state)
    assert new_version == original + 1
    assert sample_state.version == new_version


def test_validate_state_success(sample_state: State) -> None:
    """Valid state should pass validation without raising errors."""
    validate_state(sample_state)


@pytest.mark.parametrize(
    "state, message",
    [
        (State(), "prompt"),
        (State(prompt="ok", version=-1), "version"),
        (
            State(
                prompt="p",
                sources=[Citation(url="https://a"), Citation(url="https://a")],
            ),
            "citation",
        ),
    ],
)
def test_validate_state_errors(state: State, message: str) -> None:
    """Invalid state should raise a ``ValueError`` with a helpful message."""
    with pytest.raises(ValueError) as exc_info:
        validate_state(state)
    assert message in str(exc_info.value)


def test_outline_steps_concatenate_to_text() -> None:
    """Outline steps should join into newline-separated text for consumers."""
    outline = Outline(steps=["intro", "body"])
    state = State(prompt="p", outline=outline)
    assert "\n".join(state.outline.steps) == "intro\nbody"
