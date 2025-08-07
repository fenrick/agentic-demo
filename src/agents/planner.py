"""Planner node producing a high-level outline for the run."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from core.state import Outline, State
from prompts import get_prompt

from .agent_wrapper import init_chat_model
from .json_utils import load_json
from .streaming import stream_debug, stream_messages


@dataclass(slots=True)
class PlanResult:
    """Outcome of the planner step.

    Attributes:
        confidence: Heuristic score between 0 and 1 indicating planning
            certainty.
    """

    confidence: float


async def call_planner_llm(topic: str) -> str:
    """Call an LLM to produce an outline for ``topic``.

    Falls back to an empty string if the LLM client is unavailable.
    """

    try:  # pragma: no cover - exercised via monkeypatch in tests
        from pydantic_ai.messages import (
            SystemPromptPart as SystemMessage,
            UserPromptPart as HumanMessage,
        )
    except Exception:  # dependency missing
        logging.exception("Planner dependencies unavailable")
        return ""

    model = init_chat_model()
    if model is None:
        return ""
    messages = [
        SystemMessage(content=get_prompt("planner_system")),
        HumanMessage(content=topic),
    ]
    response = await model.ainvoke(messages)
    return response.content or ""


_LINE_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(.*)")


def extract_outline(text: str) -> Outline:
    """Parse bullet or numbered lines from ``text`` into an :class:`Outline`."""

    steps = []
    for line in text.splitlines():
        match = _LINE_RE.match(line)
        if match:
            steps.append(match.group(1).strip())
    return Outline(steps=steps)


async def run_planner(state: State) -> PlanResult:
    """Analyze ``state.prompt`` and draft an outline.

    The generated outline is assigned to ``state.outline`` before returning a
    minimal :class:`PlanResult` for policy evaluation.
    """

    raw = await call_planner_llm(state.prompt)
    stream_messages(raw)
    outline = Outline(steps=[])
    data = load_json(raw)
    if data is not None:
        steps = data.get("steps", [])
        if isinstance(steps, list):
            outline = Outline(steps=[str(step).strip() for step in steps])
    if not outline.steps:
        outline = extract_outline(raw)
    state.outline = outline
    confidence = 0.0
    if outline.steps:
        confidence = min(1.0, round(0.5 + 0.1 * len(outline.steps), 2))
    else:
        stream_debug("planner produced empty outline")
    return PlanResult(confidence=confidence)


__all__ = [
    "PlanResult",
    "call_planner_llm",
    "extract_outline",
    "run_planner",
]
