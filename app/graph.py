"""Conversation flow implemented with langgraph."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END, START

from .agents import plan, research, draft, review
from .overlay_agent import OverlayAgent


class GraphState(TypedDict):
    """State shared across graph nodes."""

    text: str
    draft: str
    approved: bool
    history: List[str]


@dataclass
class ConversationGraph:
    """Wrapper around a compiled langgraph."""

    graph: Any

    async def arun(self, input: str) -> Dict[str, list[str] | str]:
        """Execute the graph asynchronously."""
        state: GraphState = {
            "text": input,
            "draft": "",
            "approved": False,
            "history": [],
        }
        result: GraphState = await self.graph.ainvoke(state)
        return {"messages": result["history"], "output": result["text"]}

    def run(self, input: str) -> Dict[str, list[str] | str]:
        """Execute the graph synchronously."""
        return asyncio.run(self.arun(input))


def build_graph(overlay: Optional[OverlayAgent] = None) -> ConversationGraph:
    """Create the conversation graph using langgraph."""

    async def plan_node(state: GraphState) -> GraphState:
        text = plan(state["text"])
        return {
            "text": text,
            "draft": state["draft"],
            "approved": False,
            "history": state["history"] + [text],
        }

    async def research_node(state: GraphState) -> GraphState:
        text = research(state["text"])
        return {
            "text": text,
            "draft": state["draft"],
            "approved": False,
            "history": state["history"] + [text],
        }

    async def draft_node(state: GraphState) -> GraphState:
        text = draft(state["text"])
        return {
            "text": text,
            "draft": text,
            "approved": False,
            "history": state["history"] + [text],
        }

    async def review_node(state: GraphState) -> GraphState:
        result = review(state["text"])
        approved = "retry" not in result
        return {
            "text": result,
            "draft": state["draft"],
            "approved": approved,
            "history": state["history"] + [result],
        }

    async def overlay_node(state: GraphState) -> GraphState:
        if overlay is None:
            raise AssertionError("overlay agent missing")
        result = overlay(state["draft"], state["text"])
        return {
            "text": result,
            "draft": state["draft"],
            "approved": True,
            "history": state["history"] + [result],
        }

    builder: StateGraph = StateGraph(GraphState)
    builder.add_node("plan", plan_node)
    builder.add_node("research", research_node)
    builder.add_node("draft", draft_node)
    builder.add_node("review", review_node)
    if overlay:
        builder.add_node("overlay", overlay_node)

    builder.add_edge(START, "plan")
    builder.add_edge("plan", "research")
    builder.add_edge("research", "draft")
    builder.add_edge("draft", "review")

    def after_review(state: GraphState) -> str:
        if state["approved"]:
            return "overlay" if overlay else END
        return "draft"

    builder.add_conditional_edges("review", after_review)

    if overlay:
        builder.add_edge("overlay", END)

    graph = builder.compile()
    return ConversationGraph(graph=graph)
