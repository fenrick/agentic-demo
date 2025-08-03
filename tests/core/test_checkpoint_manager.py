"""Tests for SQLite-based checkpoint manager."""

from pathlib import Path

from core.checkpoint import SqliteCheckpointManager
from core.state import State


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    """Manager should persist and restore :class:`State`."""
    db_path = tmp_path / "checkpoint.db"
    manager = SqliteCheckpointManager(str(db_path))
    state = State(prompt="hello")
    manager.save_checkpoint(state)
    state.prompt = "changed"
    loaded = manager.load_checkpoint()
    assert loaded.prompt == "hello"
