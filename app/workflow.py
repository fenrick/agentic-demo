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

    def _clean_heading(self, line: str) -> str:
        """Remove bullet, numeric or Markdown heading prefixes from ``line``."""
        import re

        line = line.strip()
        pattern = r"^(?:[-*]|\d+(?:\.\d+)*[.)]?|#+)\s*(.*)"
        match = re.match(pattern, line)
        if match:
            return match.group(1).strip()
        return line

    def parse_outline(self, outline: str) -> List[str]:
        """Return a list of headings parsed from ``outline``."""
        return [
            self._clean_heading(line) for line in outline.splitlines() if line.strip()
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
