"""Manage progressive document edits."""

from __future__ import annotations

from dataclasses import dataclass, field
import json

from .overlay_agent import OverlayAgent
from .agents import ChatAgent


@dataclass
class MCP:
    """Master Control Program holding document state."""

    text: str = ""
    overlay: OverlayAgent = field(
        default_factory=lambda: OverlayAgent(ChatAgent(model="gpt-4.1"))
    )

    def edit(self, addition: str) -> str:
        """Integrate ``addition`` into :attr:`text`."""
        result = self.overlay(self.text, addition)
        self.text = result if isinstance(result, str) else json.dumps(result)
        return self.text
