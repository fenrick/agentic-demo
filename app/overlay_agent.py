"""Agent for overlaying additional material onto existing text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .agents import ChatAgent


@dataclass
class OverlayAgent:
    """Compose new material with existing content using a chat model."""

    agent: ChatAgent | None = None

    def __post_init__(self) -> None:
        if self.agent is None:
            self.agent = ChatAgent()

    def __call__(self, original: str, addition: str) -> str:
        """Merge new material with existing text."""
        prompt = (
            "Integrate the addition below into the existing text.\n"
            f"Existing:\n{original}\n"
            f"Addition:\n{addition}"
        )
        messages: list[Dict[str, str]] = [{"role": "user", "content": prompt}]
        assert self.agent is not None
        return self.agent(messages)
