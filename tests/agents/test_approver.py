"""Tests for the human-in-loop approver node."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_run_approver_accepts_edits(monkeypatch: pytest.MonkeyPatch) -> None:
    """Edits are applied when the user accepts them."""

    import agents.approver as approver
    from core.state import State

    events: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        approver, "stream", lambda ch, payload: events.append((ch, payload))
    )

    state = State(prompt="old")
    state.pending_edits = {"prompt": "new"}
    state.user_decision = True

    result = await approver.run_approver(state)
    assert result.accepted is True
    assert state.prompt == "new"
    assert events[0] == ("values", {"pending_edits": {"prompt": "new"}})
    assert events[1] == ("values", {"accepted": True})


@pytest.mark.asyncio
async def test_run_approver_rejects_edits(monkeypatch: pytest.MonkeyPatch) -> None:
    """State remains unchanged when the user rejects edits."""

    import agents.approver as approver
    from core.state import State

    events: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        approver, "stream", lambda ch, payload: events.append((ch, payload))
    )

    state = State(prompt="orig")
    state.pending_edits = {"prompt": "new"}
    state.user_decision = False

    result = await approver.run_approver(state)
    assert result.accepted is False
    assert state.prompt == "orig"
    assert events[0] == ("values", {"pending_edits": {"prompt": "new"}})
    assert events[1] == ("values", {"accepted": False})
