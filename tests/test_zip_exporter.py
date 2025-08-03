"""Tests for :mod:`export.zip_exporter`."""

from __future__ import annotations

import io
import json
import sqlite3
import zipfile
from pathlib import Path

from export.zip_exporter import ZipExporter


def _setup_db(path: Path) -> Path:
    db_path = path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE outlines (workspace_id TEXT, outline_json TEXT, created_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE metadata (workspace_id TEXT, topic TEXT, model TEXT, commit_sha TEXT, created_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE citations (workspace_id TEXT, url TEXT, title TEXT, retrieved_at TEXT, licence TEXT)"
    )
    outline = {
        "title": "Intro to AI",
        "objectives": ["Understand basics"],
        "activities": ["Lecture"],
        "notes": ["Remember"],
        "children": [],
    }
    conn.execute(
        "INSERT INTO outlines VALUES (?,?,?)",
        ("ws1", json.dumps(outline), "2024-01-01"),
    )
    conn.execute(
        "INSERT INTO metadata VALUES (?,?,?,?,?)",
        ("ws1", "AI", "gpt-4", "abc123", "2024-01-01"),
    )
    conn.execute(
        "INSERT INTO citations VALUES (?,?,?,?,?)",
        ("ws1", "http://example.com", "Example", "2024-01-01", None),
    )
    conn.commit()
    conn.close()
    return db_path


def test_generate_zip_contains_all_expected_files(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    exporter = ZipExporter(str(db))
    files = exporter.collect_export_files("ws1")
    data = exporter.generate_zip(files)
    assert data[:2] == b"PK"
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
    assert {"lecture.md", "lecture.docx", "lecture.pdf", "citations.json"} <= names
