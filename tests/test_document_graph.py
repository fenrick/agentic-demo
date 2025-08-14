from dataclasses import dataclass
from typing import List

from agents.models import (
    ResearchResult,
    Slide,
    SlideCopy,
    SlideSpeakerNotes,
    SlideVisualization,
)
from core import document_graph


@dataclass
class Module:
    id: str
    slides: List[Slide]


def test_build_document_dag_includes_slide_components() -> None:
    """``build_document_dag`` nests slides and notes under module nodes."""

    slide = Slide(
        slide_number=1,
        copy=SlideCopy(bullet_points=["pt"]),
        visualization=SlideVisualization(notes="viz"),
        speaker_notes=SlideSpeakerNotes(notes="spk"),
    )
    module = Module(id="m1", slides=[slide])
    research = [ResearchResult(url="u", title="t", snippet="s", keywords=["foo"])]

    dag = document_graph.build_document_dag([module], research)

    # Root links to research and module nodes
    assert [n.id for n in dag.children(dag.root)] == ["research", "m1"]

    # Research node links to keywords
    res_node = dag.children("research")[0]
    assert dag.children(res_node.id)[0].id == "research-0-keywords"

    # Slides and nested components are present
    slide_node = dag.children("m1-slides")[0]
    assert [n.id for n in dag.children(slide_node.id)] == [
        "m1-slide-1-copy",
        "m1-slide-1-visualization",
        "m1-slide-1-speaker-notes",
    ]
