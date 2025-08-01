"""Higher level document workflow utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from . import agents
from .graph import build_graph
from .overlay_agent import OverlayAgent


@dataclass
class DocumentWorkflow:
    """Orchestrate per-heading flows and return the final document."""

    overlay: OverlayAgent | None = None

    # TODO: allow nested numbering or markdown parsing of outlines
    def parse_outline(self, outline: str) -> List[str]:
        """Extract individual headings from a plain-text outline."""
        return [
            line.lstrip("- ").strip() for line in outline.splitlines() if line.strip()
        ]

    def generate(self, topic: str) -> str:
        """Generate a polished document for ``topic`` using the graph."""
        outline = agents.plan(topic)
        graph = build_graph(self.overlay, skip_plan=True)
        sections = []
        for heading in self.parse_outline(outline):
            result = graph.run(heading)
            sections.append(result["output"])
        combined = "\n\n".join(sections)
        return agents.review(combined)
