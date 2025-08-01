from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock, patch

from app import perplexity


def test_fetch_invokes_httpx():
    client = MagicMock()
    response = MagicMock()
    response.json.return_value = {"answer": "data"}
    response.text = ""
    response.raise_for_status.return_value = None
    client.get.return_value = response
    assert perplexity._fetch("x", client) == "data"
    client.get.assert_called_once_with(perplexity.API_URL, params={"q": "x"})


def test_search_caches_result(tmp_path):
    db = tmp_path / "cache.db"
    with (
        patch.object(perplexity, "DB_PATH", db),
        patch.object(perplexity, "_today", return_value="2025-08-01"),
        patch.object(perplexity, "_fetch", return_value="result") as fetch,
    ):
        first = perplexity.search("q")
        second = perplexity.search("q")
    assert first == "result" and second == "result"
    fetch.assert_called_once_with("q", client=None)
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT result FROM cache WHERE query='q'").fetchone()
    assert row[0] == "result"
    conn.close()
