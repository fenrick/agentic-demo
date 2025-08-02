"""State definitions for the lecture generation graph."""

from __future__ import annotations

from typing import List, TypedDict


class Citation(TypedDict):
    """Reference to an external resource."""

    url: str
    snippet: str


class LectureState(TypedDict):
    """Shared state passed between graph nodes."""

    topic: str
    outline: str
    citations: List[Citation]
    action_log: List[str]
    stream_buffer: List[str]
