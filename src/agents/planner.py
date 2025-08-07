"""Planner node producing a high-level outline for the run."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from core.state import Outline, State
from prompts import get_prompt

from .streaming import stream_debug, stream_messages


@dataclass(slots=True)
class PlanResult:
    """Outcome of the planner step.

    Attributes:
        confidence: Heuristic score between 0 and 1 indicating planning
            certainty.
        outline: Structured outline derived from the planner's response.
    """

    confidence: float
    outline: Outline | None = None


class PlannerOutput(BaseModel):
    """Structured schema expected from the planner model."""

    steps: list[str]


async def call_planner_llm(topic: str) -> str:
    """Call an LLM to produce an outline for ``topic``.

    Falls back to an empty string if the LLM client is unavailable.
    """

    try:  # pragma: no cover - exercised via monkeypatch in tests
        from pydantic_ai import Agent
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider
        import config
    except Exception:  # dependency missing
        logging.exception("Planner dependencies unavailable")
        return ""

    settings = config.load_settings()
    model_name = settings.model_name
    if model_name.startswith("sonar"):
        provider = OpenAIProvider(
            base_url="https://api.perplexity.ai",
            api_key=settings.perplexity_api_key,
        )
        model = OpenAIModel(model_name, provider=provider)
        agent = Agent(model, system_prompt=get_prompt("planner_system"))
    else:
        agent = Agent(
            f"openai:{model_name}", system_prompt=get_prompt("planner_system")
        )
    response = await agent.run(topic)
    return response.output or ""


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
    try:
        data = PlannerOutput.model_validate_json(raw)
        outline = Outline(steps=[step.strip() for step in data.steps])
    except (ValidationError, json.JSONDecodeError):
        outline = extract_outline(raw)
    state.outline = outline
    confidence = 0.0
    if outline.steps:
        confidence = min(1.0, round(0.5 + 0.1 * len(outline.steps), 2))
    else:
        stream_debug("planner produced empty outline")
    return PlanResult(confidence=confidence, outline=outline)


__all__ = [
    "PlanResult",
    "call_planner_llm",
    "extract_outline",
    "run_planner",
]
