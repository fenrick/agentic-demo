"""Synthesiser node streaming tokens."""

from __future__ import annotations

from ..state import LectureState
from ...prompts import get_prompt

# TODO: stream real LLM tokens derived from PROMPT.

PROMPT = get_prompt("synthesiser")


def synthesiser(state: LectureState) -> dict[str, object]:
    """Return tokens representing the lecture body.

    Tokens are split from ``app/prompts/synthesiser.txt``.
    """

    text = PROMPT.format(topic=state["topic"])
    tokens = text.split()
    message = "synthesiser: generating lecture body"
    return {
        "stream_buffer": state["stream_buffer"] + tokens,
        "action_log": state["action_log"] + [message],
    }
