"""SQLite-backed persistence for :class:`~core.state.State`."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from core.state import State, increment_version


class SqliteCheckpointManager:
    """Persist ``State`` snapshots to a SQLite database."""

    # TODO: Implement retention policy to prune old checkpoints.

    def __init__(self, db_path: str) -> None:
        """Initialize the manager with a path to the database file."""
        self._path = Path(db_path)
        self._conn = sqlite3.connect(self._path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS checkpoints (id INTEGER PRIMARY KEY AUTOINCREMENT, state TEXT NOT NULL)"
        )
        self._conn.commit()

    def save_checkpoint(self, state: State) -> None:
        """Serialize ``state`` into the checkpoint table."""
        increment_version(state)
        payload = json.dumps(state.to_dict())
        self._conn.execute("INSERT INTO checkpoints (state) VALUES (?)", (payload,))
        self._conn.commit()

    def load_checkpoint(self) -> State:
        """Load the most recent ``State`` snapshot."""
        cur = self._conn.execute(
            "SELECT state FROM checkpoints ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("No checkpoint available")
        data = json.loads(row[0])
        return State.from_dict(data)
