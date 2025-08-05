import aiosqlite
import pytest

from core.checkpoint import SqliteCheckpointManager
from core.state import State


@pytest.mark.asyncio
async def test_save_and_load_checkpoint_roundtrip(tmp_path):
    db_path = tmp_path / "checkpoints.db"
    manager = SqliteCheckpointManager(str(db_path))
    state = State(prompt="topic")
    await manager.save_checkpoint(state)
    loaded = await manager.load_checkpoint()
    assert loaded == state
    assert loaded.version == 2


@pytest.mark.asyncio
async def test_checkpoint_retention(tmp_path):
    db_path = tmp_path / "checkpoints.db"
    manager = SqliteCheckpointManager(str(db_path), max_checkpoints=2)
    for i in range(3):
        await manager.save_checkpoint(State(prompt=f"p{i}"))
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("SELECT COUNT(*) FROM checkpoints")
        row = await cur.fetchone()
    assert row[0] == 2
    loaded = await manager.load_checkpoint()
    assert loaded.prompt == "p2"
