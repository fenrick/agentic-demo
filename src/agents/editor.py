"""Agent performing editorial review over generated content."""

from __future__ import annotations

from core.state import State

from .models import EditorFeedback


async def run_editor(state: State) -> EditorFeedback:
    """Review the current state and return editorial feedback.

    This stub flags no issues and simply stores the feedback on ``state``.
    """

    feedback = EditorFeedback()
    state.editor_feedback = feedback
    return feedback


__all__ = ["run_editor"]
