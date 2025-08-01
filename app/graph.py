"""Conversation flow implemented with langgraph."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, TypedDict, cast
import json

from langgraph.graph import StateGraph, END, START
from typing import Any

from langsmith import run_helpers
from .agents import plan, research, draft, review, _log_metrics
from .overlay_agent import OverlayAgent
from .primary_agent import PrimaryAgent


class GraphState(TypedDict):
    """State shared across graph nodes."""

    text: str | dict[str, object]
    draft: str
    approved: bool
    history: List[str]
    loops: int


@dataclass
class ConversationGraph:
    """Wrapper around a compiled langgraph."""

    graph: Any

    async def arun(self, input: str) -> Dict[str, Any]:
        """Execute the graph asynchronously."""
        state: GraphState = {
            "text": input,
            "draft": "",
            "approved": False,
            "history": [],
            "loops": 0,
        }
        result: GraphState = await self.graph.ainvoke(state)
        return {"messages": result["history"], "output": result["text"]}

    def run(self, input: str) -> Dict[str, Any]:
        """Execute the graph synchronously."""
        return asyncio.run(self.arun(input))


def build_graph(
    overlay: Optional[OverlayAgent] = None,
    *,
    mode: str = "basic",
    primary: "PrimaryAgent | None" = None,
    skip_plan: bool = False,
) -> ConversationGraph:
    """Create the conversation graph using langgraph.

    Parameters
    ----------
    overlay:
        Optional :class:`OverlayAgent` for the final merge step.
    mode:
        Conversation variant. When set to ``"overlay"`` a new
        :class:`OverlayAgent` should be created if ``overlay`` is not
        provided.
    skip_plan:
        When ``True`` the returned graph starts at the research step instead of
        generating a plan first. This is useful when an outline is already
        available.
    """

    if overlay is None and mode == "overlay":
        overlay = OverlayAgent()

    @run_helpers.traceable
    async def plan_node(state: GraphState) -> GraphState:
        if primary:
            text = primary.plan(cast(str, state["text"]), loop=state["loops"])
        else:
            text = plan(cast(str, state["text"]), loop=state["loops"])
        return {
            "text": text,
            "draft": state["draft"],
            "approved": False,
            "history": state["history"] + [text],
            "loops": state["loops"],
        }

    @run_helpers.traceable
    async def research_node(state: GraphState) -> GraphState:
        if primary:
            text = primary.research(cast(str, state["text"]), loop=state["loops"])
        else:
            text = research(cast(str, state["text"]), loop=state["loops"])
        return {
            "text": text,
            "draft": state["draft"],
            "approved": False,
            "history": state["history"] + [text],
            "loops": state["loops"],
        }

    @run_helpers.traceable
    async def draft_node(state: GraphState) -> GraphState:
        if primary:
            text = primary.draft(cast(str, state["text"]), loop=state["loops"])
        else:
            text = draft(cast(str, state["text"]), loop=state["loops"])
        return {
            "text": text,
            "draft": text,
            "approved": False,
            "history": state["history"] + [text],
            "loops": state["loops"],
        }

    @run_helpers.traceable
    async def review_node(state: GraphState) -> GraphState:
        if primary:
            result = primary.review(cast(str, state["text"]), loop=state["loops"])
        else:
            result = review(cast(str, state["text"]), loop=state["loops"])
        approved = "retry" not in result
        return {
            "text": result,
            "draft": state["draft"],
            "approved": approved,
            "history": state["history"] + [result],
            "loops": state["loops"] if approved else state["loops"] + 1,
        }

    @run_helpers.traceable
    async def overlay_node(state: GraphState) -> GraphState:
        """Merge the draft with review notes and log the action."""
        assert overlay is not None
        result = overlay(state["draft"], cast(str, state["text"]))
        if isinstance(result, str):
            _log_metrics(result, state["loops"])
        else:
            _log_metrics(json.dumps(result), state["loops"])
        history_entry = (
            json.dumps(result) if isinstance(result, dict) else cast(str, result)
        )
        return {
            "text": result,
            "draft": state["draft"],
            "approved": True,
            "history": state["history"] + [history_entry],
            "loops": state["loops"],
        }

    builder: StateGraph = StateGraph(GraphState)
    if not skip_plan:
        builder.add_node("plan", plan_node)
    builder.add_node("research", research_node)
    builder.add_node("draft", draft_node)
    builder.add_node("review", review_node)
    if overlay:
        builder.add_node("overlay", overlay_node)

    if skip_plan:
        builder.add_edge(START, "research")
    else:
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
