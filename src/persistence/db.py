"""Database connection helpers."""

from __future__ import annotations

import asyncio
import sqlite3
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from config import Settings


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[sqlite3.Connection, None]:
    """Yield a connection to the application's SQLite database.

    The original project depends on :mod:`aiosqlite` for asynchronous access but
    that library is unavailable in the execution environment.  We mimic its
    behaviour using the standard :mod:`sqlite3` module wrapped in an asynchronous
    context manager.  Callers can ``await`` this function just as before, but the
    database operations themselves remain synchronous.
    """

    settings = Settings()
    db_path = settings.data_dir / "citations.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        await asyncio.sleep(0)
    finally:
        conn.close()
