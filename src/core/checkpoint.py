"""SQLite-backed persistence for :class:`~core.state.State`."""

from __future__ import annotations

import json
from pathlib import Path

import aiosqlite

from core.state import State, increment_version


class SqliteCheckpointManager:
    """Persist ``State`` snapshots to an on-disk SQLite database.

    The manager uses :mod:`aiosqlite` and opens a fresh connection for each
    operation to avoid cross-task sharing.

    Args:
        db_path: Location of the SQLite file used for persistence.
        max_checkpoints: Optional retention limit. When set, only the most
            recent ``max_checkpoints`` rows are kept in the database.
    """

    def __init__(self, db_path: str, max_checkpoints: int | None = None) -> None:
        """Store the path to the backing database file and retention limit."""
        self._path = Path(db_path)
        self._max_checkpoints = max_checkpoints

    async def save_checkpoint(self, state: State) -> None:
        """Serialize ``state`` into the checkpoint table and enforce retention."""
        increment_version(state)
        payload = json.dumps(state.to_dict())
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS checkpoints
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, state TEXT NOT NULL)"""
            )
            await db.execute("INSERT INTO checkpoints (state) VALUES (?)", (payload,))
            if self._max_checkpoints is not None:
                await db.execute(
                    """lDELETE FROM checkpoints WHERE id NOT IN
                    (SELECT id FROM checkpoints ORDER BY id DESC LIMIT ?)""",
                    (self._max_checkpoints,),
                )
            await db.commit()

    async def load_checkpoint(self) -> State:
        """Load the most recent ``State`` snapshot."""
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS checkpoints
                (id INTEGER PRIMARY KEY AUTOINCREMENT, state TEXT NOT NULL)"""
            )
            cur = await db.execute(
                "SELECT state FROM checkpoints ORDER BY id DESC LIMIT 1"
            )
            row = await cur.fetchone()
        if row is None:
            raise RuntimeError("No checkpoint available")
        data = json.loads(row[0])
        return State.from_dict(data)
