"""Planning node for the lecture graph."""

from __future__ import annotations

from ..state import LectureState
from ...prompts import get_prompt

# TODO: replace stub with LLM call using PROMPT.

PROMPT = get_prompt("planner")


def planner(state: LectureState) -> dict[str, object]:
    """Generate a simple outline for the requested topic.

    The outline template is loaded from ``app/prompts/planner.txt``.
    """

    outline = PROMPT.format(topic=state["topic"])
    message = f"planner: created outline for {state['topic']}"
    return {
        "outline": outline,
        "action_log": state["action_log"] + [message],
    }
