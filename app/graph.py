"""Conversation flow implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from .agents import plan, research, draft, review
from .overlay_agent import OverlayAgent


@dataclass
class ConversationGraph:
    """Simple sequential graph executing callables."""

    nodes: List[Callable[[str], str]]

    def run(self, input: str) -> Dict[str, str]:
        """Run the graph on the given input."""
        state = input
        history: List[str] = []
        for node in self.nodes:
            state = node(state)
            history.append(state)
        return {"messages": history, "output": state}


def build_graph(overlay: Optional[OverlayAgent] = None) -> ConversationGraph:
    """Create the default conversation graph."""

    def review_node(text: str) -> str:
        result = review(text)
        return overlay(text, result) if overlay else result

    nodes = [plan, research, draft, review_node]
    return ConversationGraph(nodes=nodes)
