"""Markdown export utilities.

This module converts :class:`~agents.models.WeaveResult` instances into a
Markdown document.  It is intentionally lightweight so that callers can
persist or display lecture plans without needing a full Markdown
framework.
"""

from __future__ import annotations

from typing import Iterable, List, Union

from agents.models import Activity, AssessmentItem, Citation, SlideBullet, WeaveResult


def render_section(title: str, content: Union[str, Iterable[str], None]) -> str:
    """Render a heading followed by bullet points or text.

    Parameters
    ----------
    title:
        Heading title for the section.
    content:
        Either a string which will be placed under the heading, an iterable of
        strings to be rendered as bullet points, or ``None`` to omit the
        section entirely.

    Returns
    -------
    str
        Formatted Markdown section or an empty string if ``content`` is empty.
    """

    if not content:
        return ""

    lines: List[str] = [f"## {title}"]
    if isinstance(content, str):
        lines.append(content)
    else:
        for item in content:
            lines.append(f"- {item}")

    return "\n".join(lines) + "\n\n"


def embed_citations(md: str, citations: List[Citation]) -> str:
    """Append citation footnotes to Markdown text.

    Each citation is referenced sequentially using the ``[^n]`` Markdown
    footnote syntax.  Callers are expected to insert ``[^n]`` markers in the
    document body in the same order.
    """

    if not citations:
        return md

    footnotes: List[str] = []
    for idx, cite in enumerate(citations, start=1):
        note = f"[^{idx}]: {cite.title} - {cite.url} (retrieved {cite.retrieved_at})"
        if cite.licence:
            note += f" — {cite.licence}"
        footnotes.append(note)

    return md + "\n" + "\n".join(footnotes) + "\n"


def _render_activities(activities: List[Activity]) -> List[str]:
    """Format activity entries for the Markdown exporter."""

    lines: List[str] = []
    for activity in activities:
        desc = f"{activity.type} ({activity.duration_min} min): {activity.description}"
        if activity.learning_objectives:
            desc += f" — objectives: {', '.join(activity.learning_objectives)}"
        lines.append(desc)
    return lines


def _render_assessment(items: List[AssessmentItem]) -> List[str]:
    """Format assessment items for Markdown output."""

    lines: List[str] = []
    for item in items:
        desc = f"{item.type}: {item.description}"
        if item.max_score is not None:
            desc += f" (max {item.max_score})"
        lines.append(desc)
    return lines


def _render_slides(slides: List[SlideBullet]) -> str:
    """Render slide bullets as individual sections."""

    sections: List[str] = []
    for slide in slides:
        sections.append(render_section(f"Slide {slide.slide_number}", slide.bullets))
    return "".join(sections)


def from_weave_result(weave: WeaveResult, citations: List[Citation]) -> str:
    """Convert a :class:`WeaveResult` and citations into Markdown.

    Parameters
    ----------
    weave:
        Structured output from the content weaver agent.
    citations:
        Citations referenced by the document.  Footnote markers ``[^n]`` are
        inserted into the "References" section following the order provided.

    Returns
    -------
    str
        A full Markdown document including YAML front-matter and citation
        footnotes.
    """

    # YAML front matter
    front_matter_lines = ["---", f"title: {weave.title}"]
    if weave.author:
        front_matter_lines.append(f"author: {weave.author}")
    if weave.date:
        front_matter_lines.append(f"date: {weave.date}")
    if weave.version:
        front_matter_lines.append(f"version: {weave.version}")
    if weave.tags:
        tags = ", ".join(weave.tags)
        front_matter_lines.append(f"tags: [{tags}]")
    front_matter_lines.append("---\n")

    doc_parts: List[str] = ["\n".join(front_matter_lines)]

    if weave.summary:
        doc_parts.append(render_section("Summary", weave.summary))

    doc_parts.append(render_section("Learning Objectives", weave.learning_objectives))

    if weave.prerequisites:
        doc_parts.append(render_section("Prerequisites", weave.prerequisites))

    if weave.activities:
        doc_parts.append(
            render_section("Activities", _render_activities(weave.activities))
        )

    if weave.slide_bullets:
        doc_parts.append(_render_slides(weave.slide_bullets))

    if weave.speaker_notes:
        doc_parts.append(render_section("Speaker Notes", weave.speaker_notes))

    if weave.assessment:
        doc_parts.append(
            render_section("Assessment", _render_assessment(weave.assessment))
        )

    if citations:
        refs = [f"[{c.title}]({c.url})[^%d]" % (i) for i, c in enumerate(citations, 1)]
        doc_parts.append(render_section("References", refs))
    elif weave.references:
        refs = [f"[{c.title}]({c.url})" for c in weave.references]
        doc_parts.append(render_section("References", refs))

    markdown = "".join(doc_parts).rstrip() + "\n"
    return embed_citations(markdown, citations)
