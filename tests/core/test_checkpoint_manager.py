"""Tests for SQLite-based checkpoint manager."""

import json
from pathlib import Path

import aiosqlite
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


@pytest.mark.asyncio
async def test_retention_prunes_old_checkpoints(tmp_path: Path) -> None:
    """Exceeding the retention limit should purge oldest snapshots."""
    db_path = tmp_path / "checkpoint.db"
    manager = SqliteCheckpointManager(str(db_path), max_checkpoints=2)
    for idx in range(3):
        await manager.save_checkpoint(State(prompt=str(idx)))

    # Only the last two checkpoints should remain in the table
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("SELECT state FROM checkpoints ORDER BY id")
        rows = await cur.fetchall()

    assert len(rows) == 2
    assert json.loads(rows[0][0])["prompt"] == "1"
    assert json.loads(rows[1][0])["prompt"] == "2"
    loaded = await manager.load_checkpoint()
    assert loaded.prompt == "2"
