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

    def plan(self, topic: str) -> str:
        """Generate an outline using the primary agent."""
        return _plan(topic, agent=self.agent)

    def research(self, outline: str) -> str:
        """Gather notes with search capability."""
        return _research(outline, agent=self.agent)

    def draft(self, notes: str) -> str:
        """Draft text from notes."""
        return _draft(notes, agent=self.agent)

    def review(self, text: str) -> str:
        """Review and polish text."""
        return _review(text, agent=self.agent)
