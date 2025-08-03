from agents.models import (
    Activity,
    AssessmentItem,
    Citation,
    SlideBullet,
    WeaveResult,
)
from export import markdown


def _sample_weave() -> WeaveResult:
    return WeaveResult(
        title="Sample Lecture",
        learning_objectives=["Objective"],
        activities=[
            Activity(
                type="Lecture",
                description="Intro",
                duration_min=5,
                learning_objectives=[],
            )
        ],
        duration_min=5,
        summary="Summary text",
        prerequisites=["Prereq"],
        slide_bullets=[SlideBullet(slide_number=1, bullets=["Point"])],
        speaker_notes="Notes",
        assessment=[AssessmentItem(type="Quiz", description="Q1")],
        references=[
            Citation(
                url="http://example.com/ref",
                title="Ref",
                retrieved_at="2024-01-01T00:00:00Z",
            )
        ],
    )


def test_from_weave_result_includes_all_sections():
    weave = _sample_weave()
    citations = [
        Citation(
            url="http://example.com/cite",
            title="Cite",
            retrieved_at="2024-01-01T00:00:00Z",
        )
    ]
    md = markdown.from_weave_result(weave, citations)
    assert "title: Sample Lecture" in md
    assert "## Summary" in md
    assert "## Learning Objectives" in md
    assert "## Prerequisites" in md
    assert "## Activities" in md
    assert "## Slide 1" in md
    assert "## Speaker Notes" in md
    assert "## Assessment" in md
    assert "## References" in md
    assert "[^1]: Cite - http://example.com/cite" in md


def test_embed_citations_generates_footnotes():
    md = "Body text\n"
    citations = [
        Citation(url="http://a", title="A", retrieved_at="2024-01-01T00:00:00Z"),
        Citation(
            url="http://b",
            title="B",
            retrieved_at="2024-01-02T00:00:00Z",
            licence="CC-BY",
        ),
    ]
    result = markdown.embed_citations(md, citations)
    assert "[^1]: A - http://a (retrieved 2024-01-01T00:00:00Z)" in result
    assert "[^2]: B - http://b (retrieved 2024-01-02T00:00:00Z) — CC-BY" in result
