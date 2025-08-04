"""Tests for the citation repository."""

from __future__ import annotations

from datetime import datetime

import pytest

from persistence import Citation, CitationRepo, get_db_session

CREATE_TABLE_SQL = """
CREATE TABLE citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    licence TEXT NOT NULL
)
"""


@pytest.mark.asyncio
async def test_insert_and_get_by_url(tmp_path, monkeypatch):
    """Inserting then fetching a citation returns the same record."""

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "x")
    monkeypatch.setenv("MODEL_NAME", "model")
    async with get_db_session() as conn:
        await conn.execute(CREATE_TABLE_SQL)
        await conn.commit()
        repo = CitationRepo(conn, "ws1")
        citation = Citation(
            url="https://example.com",
            title="Example",
            retrieved_at=datetime.utcnow(),
            licence="CC0",
        )
        await repo.insert(citation)
        fetched = await repo.get_by_url(str(citation.url))
        assert fetched == citation


@pytest.mark.asyncio
async def test_list_by_workspace(tmp_path, monkeypatch):
    """Listing citations returns only those for the requested workspace."""

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "x")
    monkeypatch.setenv("MODEL_NAME", "model")
    async with get_db_session() as conn:
        await conn.execute(CREATE_TABLE_SQL)
        await conn.commit()
        repo1 = CitationRepo(conn, "ws1")
        repo2 = CitationRepo(conn, "ws2")
        citation1 = Citation(
            url="https://a.example.com",
            title="A",
            retrieved_at=datetime.utcnow(),
            licence="L1",
        )
        citation2 = Citation(
            url="https://b.example.com",
            title="B",
            retrieved_at=datetime.utcnow(),
            licence="L2",
        )
        await repo1.insert(citation1)
        await repo2.insert(citation2)
        ws1 = await repo1.list_by_workspace("ws1")
        ws2 = await repo2.list_by_workspace("ws2")
        assert ws1 == [citation1]
        assert ws2 == [citation2]
