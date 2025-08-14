"""Section-wise document generation using a simple graph iterator."""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field

from agents.models import ResearchResult

# ---------------------------------------------------------------------------
# Legacy graph implementation retained temporarily for reference.
# The orchestrator now drives content generation, so this class is commented
# out and slated for removal once dependent code is migrated.
# ---------------------------------------------------------------------------
# from dataclasses import dataclass
# from typing import Awaitable, Callable
# from core.state import State
#
# NodeCallable = Callable[[State], Awaitable[object]]
#
# @dataclass
# class DocumentGraph:
#     """Lightweight graph executor for document generation."""
#
#     nodes: List[NodeCallable]
#
#     async def run(self, state: State) -> None:
#         for node in self.nodes:
#             await node(state)


class DocumentNode(BaseModel):
    """Content node tracked within the :class:`DocumentDAG`."""

    id: str
    type: str
    content: object | None = None


class DocumentDAG(BaseModel):
    """Directed acyclic graph capturing document structure."""

    root: str = "root"
    nodes: Dict[str, DocumentNode] = Field(default_factory=dict)
    edges: Dict[str, List[str]] = Field(default_factory=dict)

    def add_node(self, node: DocumentNode) -> None:
        self.nodes[node.id] = node
        self.edges.setdefault(node.id, [])

    def add_edge(self, parent: str, child: str) -> None:
        self.edges.setdefault(parent, []).append(child)

    def children(self, node_id: str) -> List[DocumentNode]:
        return [self.nodes[c] for c in self.edges.get(node_id, [])]


def build_document_dag(
    modules: List[object], research: List[ResearchResult] | None = None
) -> DocumentDAG:
    """Embed ``modules`` and research results into a document DAG.

    Args:
        modules: Session modules, each exposing ``id`` and optional ``slides``.
        research: Optional research results with keywords.

    Returns:
        DocumentDAG: Rooted DAG with research, module, slide, and note nodes.
    """

    dag = DocumentDAG()
    dag.add_node(DocumentNode(id=dag.root, type="document"))

    if research:
        dag.add_node(DocumentNode(id="research", type="research"))
        dag.add_edge(dag.root, "research")
        for idx, res in enumerate(research):
            res_id = f"research-{idx}"
            dag.add_node(DocumentNode(id=res_id, type="research_result", content=res))
            dag.add_edge("research", res_id)
            kw_id = f"{res_id}-keywords"
            dag.add_node(
                DocumentNode(id=kw_id, type="research_keywords", content=res.keywords)
            )
            dag.add_edge(res_id, kw_id)

    for module in modules:
        mod_id = getattr(module, "id", "")
        mod_node = DocumentNode(id=mod_id, type="module", content=module)
        dag.add_node(mod_node)
        dag.add_edge(dag.root, mod_id)

        slides_container = f"{mod_id}-slides"
        dag.add_node(DocumentNode(id=slides_container, type="slides"))
        dag.add_edge(mod_id, slides_container)

        for slide in getattr(module, "slides", []) or []:
            slide_num = getattr(
                slide, "slide_number", len(dag.edges[slides_container]) + 1
            )
            slide_id = f"{mod_id}-slide-{slide_num}"
            slide_node = DocumentNode(id=slide_id, type="slide", content=slide)
            dag.add_node(slide_node)
            dag.add_edge(slides_container, slide_id)

            if getattr(slide, "copy", None) is not None:
                copy_id = f"{slide_id}-copy"
                dag.add_node(
                    DocumentNode(id=copy_id, type="slide_copy", content=slide.copy)
                )
                dag.add_edge(slide_id, copy_id)
            if getattr(slide, "visualization", None) is not None:
                vis_id = f"{slide_id}-visualization"
                dag.add_node(
                    DocumentNode(
                        id=vis_id,
                        type="slide_visualization",
                        content=slide.visualization,
                    )
                )
                dag.add_edge(slide_id, vis_id)
            if getattr(slide, "speaker_notes", None) is not None:
                notes_id = f"{slide_id}-speaker-notes"
                dag.add_node(
                    DocumentNode(
                        id=notes_id,
                        type="slide_speaker_notes",
                        content=slide.speaker_notes,
                    )
                )
                dag.add_edge(slide_id, notes_id)
    return dag


__all__ = ["DocumentNode", "DocumentDAG", "build_document_dag"]
