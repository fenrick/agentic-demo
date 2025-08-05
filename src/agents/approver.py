"""Human-in-loop approver node."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from core.state import ActionLog, State

from .streaming import stream


@dataclass(slots=True)
class StateEdits:
    """Editable deltas awaiting user acceptance."""

    accepted: bool = True


async def run_approver(state: State) -> StateEdits:
    """Expose edits to the user and await confirmation.

    The function expects two optional attributes on ``state``:

    ``pending_edits``
        Mapping of attribute names to proposed new values.
    ``user_decision``
        Boolean flag supplied by the UI indicating whether the edits should be
        applied. Defaults to ``True`` when not provided.
    """

    edits: Dict[str, Any] = getattr(state, "pending_edits", {})
    stream("values", {"pending_edits": edits})
    accepted = getattr(state, "user_decision", True)
    if accepted:
        for key, value in edits.items():
            setattr(state, key, value)
    stream("values", {"accepted": accepted})
    state.log.append(
        ActionLog(message=f"Edits {'accepted' if accepted else 'rejected'}")
    )
    state.pending_edits = {}
    return StateEdits(accepted=accepted)
