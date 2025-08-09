"""Async SQLite database utilities.

This module provides helpers to initialize the application's SQLite database and
obtain connections for use within request handlers.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite
from alembic import command  # type: ignore[import]
from alembic.config import Config  # type: ignore[import]

from config import Settings, load_settings


async def init_db(settings: Settings | None = None) -> Path:
    """Initialize the workspace database and run migrations.

    Parameters
    ----------
    settings:
        Optional pre-loaded :class:`Settings`. When ``None`` the global settings
        are loaded.

    Returns
    -------
    Path
        Filesystem location of the SQLite database.
    """

    settings = settings or load_settings()
    db_url = settings.database_url or f"sqlite:///{settings.data_dir / 'workspace.db'}"
    if not db_url.startswith("sqlite:///"):
        raise ValueError("Only SQLite URLs are supported.")
    db_path = Path(db_url.replace("sqlite:///", ""))
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure the database file exists before running migrations.
    async with aiosqlite.connect(db_path):
        pass

    # Configure Alembic to target this database path and apply migrations.
    alembic_cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")
    return db_path


@asynccontextmanager
async def get_db_session(
    db_path: Path | None = None,
) -> AsyncGenerator[aiosqlite.Connection, None]:
    """Yield an :class:`aiosqlite.Connection` to the workspace database."""

    if db_path is None:
        settings = load_settings()
        db_url = (
            settings.database_url or f"sqlite:///{settings.data_dir / 'workspace.db'}"
        )
        if not db_url.startswith("sqlite:///"):
            raise ValueError("Only SQLite URLs are supported.")
        db_path = Path(db_url.replace("sqlite:///", ""))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(db_path)
    try:
        yield conn
    finally:
        await conn.close()
