"""Agent for overlaying additional material onto existing text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
import json

from . import utils

from .agents import ChatAgent


@dataclass
class OverlayAgent:
    """Compose new material with existing content using a chat model."""

    agent: ChatAgent | None = None

    def __post_init__(self) -> None:
        if self.agent is None:
            self.agent = ChatAgent()

    def __call__(self, original: str, addition: str) -> str | dict[str, object]:
        """Merge new material with existing text. JSON responses are parsed to a dictionary."""
        # TODO: use YAML template for overlay prompt
        template = utils.load_prompt("overlay")
        prompt = template.format(original=original, addition=addition)
        system = utils.load_prompt("system")
        user = utils.load_prompt("user").format(input=prompt)
        messages: list[Dict[str, str]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        assert self.agent is not None
        result = self.agent(messages)
        try:
            return json.loads(result)
        except Exception:
            return result
