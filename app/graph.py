"""Conversation flow implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .agents import ChatAgent
from .utils import load_prompt


@dataclass
class ConversationGraph:
    """Simplistic sequential graph for conversation."""

    agent: ChatAgent

    def run(self, input: str) -> Dict[str, str]:
        """Execute the conversation flow.

        Parameters
        ----------
        input : str
            User input.

        Returns
        -------
        dict
            State containing the assistant output and message history.
        """
        system = load_prompt("system")
        user = load_prompt("user").format(input=input)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        reply = self.agent(messages)
        messages.append({"role": "assistant", "content": reply})
        return {"messages": messages, "output": reply}


def build_graph() -> ConversationGraph:
    """Factory for a :class:`ConversationGraph`."""
    return ConversationGraph(agent=ChatAgent())
