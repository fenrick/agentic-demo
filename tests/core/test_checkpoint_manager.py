"""Tests for SQLite-based checkpoint manager."""

from pathlib import Path

import pytest

from core.checkpoint import SqliteCheckpointManager
from core.state import State


@pytest.mark.asyncio
async def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    """Manager should persist and restore :class:`State`."""
    db_path = tmp_path / "checkpoint.db"
    manager = SqliteCheckpointManager(str(db_path))
    state = State(prompt="hello")
    await manager.save_checkpoint(state)
    state.prompt = "changed"
    loaded = await manager.load_checkpoint()
    assert loaded.prompt == "hello"
