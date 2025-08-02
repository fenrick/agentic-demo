"""Assemble the lecture generation graph."""

from __future__ import annotations

from typing import Any
from langgraph.graph import StateGraph, START, END

from .state import LectureState
from .nodes.planner import planner
from .nodes.researcher import researcher
from .nodes.synthesiser import synthesiser
from .nodes.pedagogy_critic import pedagogy_critic
from .nodes.qa_reviewer import qa_reviewer


def build_graph() -> Any:
    """Return a compiled LangGraph for the lecture pipeline."""

    return (
        StateGraph(LectureState)
        .add_node("planner", planner)
        .add_node("research", researcher)
        .add_node("synth", synthesiser)
        .add_node("pedagogy", pedagogy_critic)
        .add_node("qa", qa_reviewer)
        .add_edge(START, "planner")
        .add_edge("planner", "research")
        .add_edge("research", "synth")
        .add_edge("synth", "pedagogy")
        .add_edge("pedagogy", "qa")
        .add_edge("qa", END)
        .compile()
    )
