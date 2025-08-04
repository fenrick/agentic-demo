from pathlib import Path

import aiosqlite
import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph

from core.state import Outline, State
from persistence.manager import PersistenceManager


@pytest.mark.asyncio
async def test_resume_from_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Graph run can resume and exporter generates Markdown from restored outline."""
    for key in ("OPENAI_API_KEY", "PERPLEXITY_API_KEY", "MODEL_NAME"):
        monkeypatch.setenv(key, "x")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    pm = PersistenceManager()

    async def content_weaver(state: State) -> State:
        state.outline = Outline(steps=["step1", "step2"])
        await pm.checkpoint(state, state.outline)
        return state

    async def exporter(state: State) -> str:
        return "\n".join(f"- {s}" for s in state.outline.steps)

    graph = StateGraph(State)
    graph.add_node("Content-Weaver", content_weaver)
    graph.add_node("Exporter", exporter)
    graph.add_edge(START, "Content-Weaver")
    graph.add_edge("Content-Weaver", "Exporter")
    graph.add_edge("Exporter", END)

    conn = await aiosqlite.connect(tmp_path / "graph.db")
    saver = AsyncSqliteSaver(conn)
    compiled = graph.compile(checkpointer=saver)
    config: RunnableConfig = {"configurable": {"thread_id": "t1"}}

    await compiled.ainvoke(
        State(prompt="hello"), config=config, interrupt_after=["Content-Weaver"]
    )

    restored_state, restored_outline = await pm.restore()
    assert restored_state.prompt == "hello"
    assert restored_outline.steps == ["step1", "step2"]

    md = await compiled.ainvoke(None, config=config, resume=True)
    assert md.strip() != ""
    assert "- step1" in md
