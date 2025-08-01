"""Primary agent orchestrating other agents."""

from __future__ import annotations

from dataclasses import dataclass, field

from .agents import (
    ChatAgent,
    plan as _plan,
    research as _research,
    draft as _draft,
    review as _review,
)


@dataclass
class PrimaryAgent:
    """Control agent configured with GPT-4.1."""

    agent: ChatAgent = field(default_factory=lambda: ChatAgent(model="gpt-4.1"))

    def plan(self, topic: str, *, loop: int = 0) -> str:
        """Generate an outline using the primary agent."""
        return _plan(topic, agent=self.agent, loop=loop)

    def research(self, outline: str, *, loop: int = 0) -> str:
        """Gather notes with search capability."""
        return _research(outline, agent=self.agent, loop=loop)

    def draft(self, notes: str, *, loop: int = 0) -> str:
        """Draft text from notes."""
        return _draft(notes, agent=self.agent, loop=loop)

    def review(self, text: str, *, loop: int = 0) -> str:
        """Review and polish text."""
        return _review(text, agent=self.agent, loop=loop)
