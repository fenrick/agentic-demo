"""Integration test for graph checkpointing and resume."""

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from agentic_demo.orchestration import create_state_graph
from core.state import State


def test_resume_from_checkpoint(tmp_path: Path) -> None:
    """Graph run can be interrupted and later resumed with prior state."""
    db_path = tmp_path / "checkpoints.sqlite"
    conn = sqlite3.connect(db_path, check_same_thread=False)
    saver = SqliteSaver(conn)
    app = create_state_graph().compile(checkpointer=saver)
    config = {"configurable": {"thread_id": "t1"}}

    partial = app.invoke(
        State(prompt="question"), config=config, interrupt_after=["planner"]
    )
    assert partial["log"] == [{"message": "planner"}]

    snapshot = app.get_state(config)
    assert snapshot.values["log"] == [{"message": "planner"}]

    final = app.invoke(None, config=config, resume=True)
    assert final["log"][0] == {"message": "planner"}
    assert final["log"][-1] == {"message": "exporter"}
    conn.close()
