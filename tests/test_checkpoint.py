"""Integration test for checkpoint resume behavior."""

from __future__ import annotations

from pathlib import Path

import aiosqlite
import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph

from core.state import ActionLog, State


@pytest.mark.asyncio
async def test_resume_from_checkpoint(tmp_path: Path) -> None:
    """Graph run can be interrupted and later resumed with prior state."""

    async def first(state: State) -> State:
        state.log.append(ActionLog(message="first"))
        return state

    async def second(state: State) -> State:
        state.log.append(ActionLog(message="second"))
        return state

    graph = StateGraph(State)
    graph.add_node("first", first)
    graph.add_node("second", second)
    graph.add_edge(START, "first")
    graph.add_edge("first", "second")
    graph.add_edge("second", END)

    db_path = tmp_path / "checkpoint.db"
    conn = await aiosqlite.connect(db_path)
    saver = AsyncSqliteSaver(conn)
    compiled = graph.compile(checkpointer=saver)
    config: RunnableConfig = {"configurable": {"thread_id": "t1"}}

    await compiled.ainvoke(
        State(prompt="q"),  # type: ignore[arg-type]
        config=config,
        interrupt_after=["first"],
    )
    assert db_path.exists()

    snapshot = await compiled.aget_state(config)
    assert [entry.message for entry in snapshot.values["log"]] == ["first"]

    final = await compiled.ainvoke(None, config=config, resume=True)
    assert [entry.message for entry in final["log"]] == ["first", "second"]
