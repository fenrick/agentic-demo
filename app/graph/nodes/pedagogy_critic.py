"""Pedagogy critic node."""

from __future__ import annotations

from ..state import LectureState
from ...prompts import get_prompt

# TODO: evaluate pedagogy using LLM and PROMPT.

PROMPT = get_prompt("pedagogy_critic")


def pedagogy_critic(state: LectureState) -> dict[str, object]:
    """Log pedagogical review."""

    message = PROMPT.format(topic=state["topic"])
    return {
        "action_log": state["action_log"] + [message],
    }
