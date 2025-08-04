"""Planner node producing a high-level outline for the run."""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.state import Outline, State
from prompts import get_prompt

from .agent_wrapper import get_llm_params


@dataclass(slots=True)
class PlanResult:
    """Outcome of the planner step.

    Attributes:
        outline: Planned outline generated from the topic.
        confidence: Heuristic score between 0 and 1 indicating planning certainty.
    """

    outline: Outline
    confidence: float


async def call_planner_llm(topic: str) -> str:
    """Call an LLM to produce an outline for ``topic``.

    Falls back to an empty string if the LLM client is unavailable.
    """

    try:  # pragma: no cover - exercised via monkeypatch in tests
        from langchain_openai import ChatOpenAI  # type: ignore
        from langchain_core.messages import HumanMessage, SystemMessage
    except Exception:  # dependency missing
        return ""

    model = ChatOpenAI(**get_llm_params())
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
    """Analyze ``state.prompt`` and draft an outline."""

    raw = await call_planner_llm(state.prompt)
    outline = extract_outline(raw)
    confidence = 0.0
    if outline.steps:
        confidence = min(1.0, round(0.5 + 0.1 * len(outline.steps), 2))
    return PlanResult(outline=outline, confidence=confidence)


__all__ = [
    "PlanResult",
    "call_planner_llm",
    "extract_outline",
    "run_planner",
]
