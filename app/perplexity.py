"""Perplexity search integration with SQLite caching."""

from __future__ import annotations

import pathlib
import sqlite3
from datetime import date
from typing import Any

import httpx

# Path to the SQLite database used for caching
DB_PATH = pathlib.Path(__file__).parent / "perplexity_cache.db"

API_URL = "https://api.perplexity.ai/search"


def _today() -> str:
    """Return the current date as ``YYYY-MM-DD``."""

    return date.today().isoformat()


def _ensure_db() -> sqlite3.Connection:
    """Return a connection to the cache creating the table if needed."""

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS cache (query TEXT, date TEXT, result TEXT, "
        "PRIMARY KEY(query, date))"
    )
    return conn


def _fetch(query: str, client: httpx.Client | None = None) -> str:
    """Fetch search results from Perplexity for ``query``."""

    http_client = client or httpx.Client()
    resp = http_client.get(API_URL, params={"q": query})
    resp.raise_for_status()
    data: Any = resp.json()
    if client is None:
        http_client.close()
    return data.get("answer", data.get("text", resp.text))


def search(query: str, *, client: httpx.Client | None = None) -> str:
    """Return cached Perplexity results for ``query``."""

    conn = _ensure_db()
    day = _today()
    row = conn.execute(
        "SELECT result FROM cache WHERE query=? AND date=?", (query, day)
    ).fetchone()
    if row:
        conn.close()
        return row[0]

    result = _fetch(query, client=client)
    conn.execute(
        "INSERT OR REPLACE INTO cache(query, date, result) VALUES (?, ?, ?)",
        (query, day, result),
    )
    conn.commit()
    conn.close()
    return result
