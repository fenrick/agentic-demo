"""Human-in-loop approver node."""

from __future__ import annotations

from dataclasses import dataclass

from core.state import State


@dataclass(slots=True)
class StateEdits:
    """Editable deltas awaiting user acceptance."""

    accepted: bool = True


async def run_approver(state: State) -> StateEdits:
    """Expose edits to the user and await confirmation.

    TODO: Hook into UI for manual review.
    """

    return StateEdits()
