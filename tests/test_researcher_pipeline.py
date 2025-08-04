import asyncio
from contextlib import asynccontextmanager

import aiosqlite

from agents.researcher_pipeline import researcher_pipeline
from agents.researcher_web import CitationDraft
from core.state import State

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


def test_researcher_pipeline_persists(monkeypatch, tmp_path):
    async def run() -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "sk")
        monkeypatch.setenv("PERPLEXITY_API_KEY", "pk")
        monkeypatch.setenv("MODEL_NAME", "gpt")
        monkeypatch.setenv("DATA_DIR", str(tmp_path))
        monkeypatch.setenv("ALLOWLIST_DOMAINS", '["example.com"]')

        db_file = tmp_path / "citations.db"

        @asynccontextmanager
        async def fake_get_db_session():
            conn = await aiosqlite.connect(db_file)
            await conn.execute(CREATE_TABLE_SQL)
            await conn.commit()
            try:
                yield conn
            finally:
                await conn.close()

        monkeypatch.setattr(
            "agents.researcher_pipeline.get_db_session", fake_get_db_session
        )

        drafts = [
            CitationDraft(url="http://example.com/a", snippet="", title="A"),
            CitationDraft(url="http://other.com/b", snippet="", title="B"),
        ]

        def fake_run_web_search(state):
            return drafts

        monkeypatch.setattr(
            "agents.researcher_pipeline.run_web_search", fake_run_web_search
        )

        class DummyResponse:
            headers = {"License": "CC0"}

        monkeypatch.setattr(
            "agents.researcher_pipeline.httpx.head",
            lambda url, timeout=5.0: DummyResponse(),
        )

        state = State(prompt="")
        results = await researcher_pipeline("query", state)
        assert len(results) == 1
        assert str(results[0].url) == "http://example.com/a"

        async with aiosqlite.connect(db_file) as check:
            cur = await check.execute("SELECT url FROM citations")
            rows = await cur.fetchall()
            assert rows == [("http://example.com/a",)]
            await cur.close()

    asyncio.run(run())
