"""Graph orchestration utilities."""

from __future__ import annotations

from pathlib import Path
import sqlite3

from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from agentic_demo.config import Settings

try:  # pragma: no cover - import path varies with package version
    from langgraph_checkpoint_sqlite import SqliteCheckpointSaver  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from langgraph.checkpoint.sqlite import SqliteSaver as SqliteCheckpointSaver


# TODO: Handle alternative checkpoint backends beyond SQLite.


def compile_with_sqlite_checkpoint(
    graph: StateGraph, data_dir: Path | None = None
) -> CompiledStateGraph:
    """Compile ``graph`` with SQLite-backed checkpointing.

    Purpose:
        Ensure graphs persist state between runs using a SQLite checkpoint saver.

    Inputs:
        graph: StateGraph to compile.
        data_dir: Optional directory for database storage. Defaults to ``Settings.DATA_DIR``.

    Outputs:
        Compiled graph configured with a SQLite checkpoint saver.

    Side Effects:
        Creates ``data_dir`` and a ``checkpoint.db`` file if absent.

    Exceptions:
        Propagates from file system access or graph compilation.
    """

    data_dir = data_dir or Settings().DATA_DIR  # type: ignore[call-arg]
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "checkpoint.db"

    try:
        saver = SqliteCheckpointSaver(path=str(db_path))  # type: ignore[arg-type]
    except TypeError:  # pragma: no cover - fallback for older API
        conn = sqlite3.connect(db_path, check_same_thread=False)
        saver = SqliteCheckpointSaver(conn)  # type: ignore[arg-type]

    return graph.compile(checkpointer=saver)
