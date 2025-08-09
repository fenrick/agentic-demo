"""Repository for persisting :class:`~core.state.State` objects."""

from __future__ import annotations

import json
from datetime import datetime

import aiosqlite

from ...core.state import State


class StateRepo:
    """CRUD helpers for the ``state`` table."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def save_state(self, state: State) -> int:
        """Persist ``state`` and return its identifier.

        The state's ``version`` is used as both the ``id`` and ``version``
        columns, enabling deterministic lookups.
        """
        payload = json.dumps(state.to_dict())
        now = datetime.utcnow().isoformat()
        await self._conn.execute(
            """
            INSERT INTO state (id, payload_json, version, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                payload_json=excluded.payload_json,
                version=excluded.version,
                updated_at=excluded.updated_at
            """,
            (state.version, payload, state.version, now),
        )
        await self._conn.commit()
        return state.version

    async def get_latest_state(self) -> State:
        """Return the most recently saved state."""
        cur = await self._conn.execute(
            "SELECT payload_json FROM state ORDER BY version DESC LIMIT 1"
        )
        row = await cur.fetchone()
        await cur.close()
        if row is None:
            raise ValueError("no state rows found")
        data = json.loads(row[0])
        return State.from_dict(data)

    async def get_state_by_version(self, version: int) -> State:
        """Load a specific state version."""
        cur = await self._conn.execute(
            "SELECT payload_json FROM state WHERE version = ?",
            (version,),
        )
        row = await cur.fetchone()
        await cur.close()
        if row is None:
            raise ValueError(f"state version {version} not found")
        data = json.loads(row[0])
        return State.from_dict(data)

    async def list_versions(self) -> list[int]:
        """Return all persisted state versions sorted ascending."""
        cur = await self._conn.execute("SELECT version FROM state ORDER BY version")
        rows = await cur.fetchall()
        await cur.close()
        return [row[0] for row in rows]
