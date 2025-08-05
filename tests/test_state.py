import pytest

from datetime import datetime

from core.state import (
    ActionLog,
    Citation,
    Module,
    Outline,
    State,
    increment_version,
    validate_state,
)


def test_increment_version():
    state = State(prompt="topic")
    new_version = increment_version(state)
    assert new_version == 2
    assert state.version == 2


def test_to_dict_from_dict_roundtrip():
    state = State(
        prompt="topic",
        sources=[Citation(url="https://example.com")],
        outline=Outline(
            steps=["step1"],
            learning_objectives=["lo"],
            modules=[Module(id="m1", title="Intro", duration_min=10)],
        ),
        log=[ActionLog(message="started")],
        retries={"node": 1},
        retry_counts={"section": 2},
        learning_objectives=["objective"],
        modules=[Module(id="m2", title="Body", duration_min=20)],
    )
    raw = state.to_dict()
    restored = State.from_dict(raw)
    assert restored.to_dict() == state.to_dict()


def test_validate_state_success():
    state = State(prompt="topic", sources=[Citation(url="https://example.com")])
    validate_state(state)


def test_action_log_defaults():
    entry = ActionLog(message="hello")
    assert entry.level == "INFO"
    assert isinstance(entry.timestamp, datetime)


@pytest.mark.parametrize(
    "modifier",
    [
        lambda s: setattr(s, "prompt", ""),
        lambda s: setattr(s, "version", -1),
        lambda s: s.sources.extend(
            [Citation(url="https://dup"), Citation(url="https://dup")]
        ),
    ],
)
def test_validate_state_errors(modifier):
    state = State(prompt="topic")
    modifier(state)
    with pytest.raises(ValueError):
        validate_state(state)
