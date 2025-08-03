"""Database connection helpers."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiosqlite

from config import Settings


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Yield a connection to the application's SQLite database."""

    settings = Settings()
    db_path = settings.data_dir / "citations.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(db_path)
    try:
        yield conn
    finally:
        await conn.close()
