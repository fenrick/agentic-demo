"""State model for orchestration core."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class State:
    """Represents the evolving state of a LangGraph conversation.

    Attributes:
        prompt: Latest user or system prompt driving the conversation.
        sources: Collection of source identifiers used for context.
        outline: High level plan or outline guiding the conversation.
        log: History of notable events or messages.
        version: Integer representing the schema version of this state.
        confidence: Planner's confidence in the current plan.
        critic_score: Latest score assigned by the critic.
        critic_attempts: Number of times the critic has evaluated the content.
    """

    prompt: str = ""
    sources: List[str] = field(default_factory=list)
    outline: List[str] = field(default_factory=list)
    log: List[str] = field(default_factory=list)
    version: int = 1
    confidence: float = 0.0
    critic_score: float = 0.0
    critic_attempts: int = 0
