"""Tests for the web UI and download endpoints."""

from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient
from typing import cast

from app.api import app
from app import db

client = TestClient(app)


def _seed_run(conn: sqlite3.Connection, topic: str, body: str) -> int:
    cur = conn.execute(
        "INSERT INTO runs(topic, started_at, finished_at) VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
        (topic,),
    )
    run_id = cast(int, cur.lastrowid)
    conn.execute(
        "INSERT INTO versions(run_id, step, body_markdown, created_at) VALUES (?, 1, ?, CURRENT_TIMESTAMP)",
        (run_id, body),
    )
    conn.commit()
    return run_id


def test_index_has_expected_elements() -> None:
    """Index page should expose topic input and controls."""
    resp = client.get("/")
    assert resp.status_code == 200
    text = resp.text
    assert "<input" in text and "topic" in text
    assert "cancel" in text.lower()
    assert "download" in text.lower()


def test_download_endpoints_return_content(tmp_path: str) -> None:
    """Markdown, DOCX and PDF downloads must return content."""
    conn = db.connect()
    run_id = _seed_run(conn, "Test", "Hello world")
    for fmt, ctype in [
        ("md", "text/markdown"),
        (
            "docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        ("pdf", "application/pdf"),
    ]:
        resp = client.get(f"/runs/{run_id}/download/{fmt}")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith(ctype)
        assert resp.content  # non-empty


def test_stream_includes_token_and_logs() -> None:
    """Stream should yield log and token events."""
    conn = db.connect()
    run_id = _seed_run(conn, "Topic", "token1 token2")
    with client.stream("GET", f"/runs/{run_id}/stream") as resp:
        text = "".join(list(resp.iter_text())[:4])
        assert "event: log" in text
        assert "event: token" in text
