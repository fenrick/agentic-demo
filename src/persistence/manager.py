"""High level checkpoint and restore operations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import aiosqlite

from config import Settings
from core.state import Outline, State

from .parquet_serializer import ParquetSerializer
from .repos.document_repo import DocumentRepo
from .repos.state_repo import StateRepo


class PersistenceManager:
    """Coordinate persistence of state and outline documents."""

    def __init__(self) -> None:
        settings = Settings()
        db_url = (
            settings.database_url or f"sqlite:///{settings.data_dir / 'workspace.db'}"
        )
        if not db_url.startswith("sqlite:///"):
            raise ValueError("PersistenceManager supports only SQLite.")
        self._db_path: Path = Path(db_url.replace("sqlite:///", ""))
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    async def checkpoint(self, state: State, outline: Outline) -> None:
        """Persist ``state`` and ``outline`` as a new version."""
        async with aiosqlite.connect(self._db_path) as conn:
            state_repo = StateRepo(conn)
            state_id = await state_repo.save_state(state)
            blob = ParquetSerializer.serialize_outline(outline)
            doc_repo = DocumentRepo(conn)
            await doc_repo.save_document_version(state_id, blob)

    async def restore(self, version: Optional[int] = None) -> Tuple[State, Outline]:
        """Return a previously persisted state and outline."""
        async with aiosqlite.connect(self._db_path) as conn:
            state_repo = StateRepo(conn)
            if version is None:
                state = await state_repo.get_latest_state()
                version = state.version
            else:
                state = await state_repo.get_state_by_version(version)
            doc_repo = DocumentRepo(conn)
            blob = await doc_repo.load_latest_document(version)
            outline = ParquetSerializer.deserialize_outline(blob)
            return state, outline
