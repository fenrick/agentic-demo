"""Researcher node providing citations."""

from __future__ import annotations

from ..state import LectureState, Citation
from ...prompts import get_prompt

# TODO: implement actual research using PROMPT with external sources.

PROMPT = get_prompt("researcher")


def researcher(state: LectureState) -> dict[str, object]:
    """Attach a placeholder citation."""

    snippet = PROMPT.format(topic=state["topic"])
    citation: Citation = {
        "url": "https://example.com",
        "snippet": snippet,
    }
    message = f"researcher: gathered citation for {state['topic']}"
    return {
        "citations": state["citations"] + [citation],
        "action_log": state["action_log"] + [message],
    }
