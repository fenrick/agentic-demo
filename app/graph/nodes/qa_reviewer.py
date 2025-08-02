"""QA reviewer node."""

from __future__ import annotations

from ..state import LectureState
from ...prompts import get_prompt

# TODO: perform final QA using PROMPT.

PROMPT = get_prompt("qa_reviewer")


def qa_reviewer(state: LectureState) -> dict[str, object]:
    """Log quality assurance review."""

    message = PROMPT.format(topic=state["topic"])
    return {
        "action_log": state["action_log"] + [message],
    }
