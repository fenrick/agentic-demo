import sqlite3
import pytest

import app.db as db


@pytest.fixture
def fresh_db(tmp_path):
    path = tmp_path / "test.db"
    conn = db.connect(str(path))
    db._CONN = conn  # ensure wrappers use this connection
    yield conn
    conn.close()
    db._CONN = None


def test_connection_enables_wal_and_foreign_keys(fresh_db):
    mode = fresh_db.execute("PRAGMA journal_mode;").fetchone()[0]
    assert mode.lower() == "wal"
    fk = fresh_db.execute("PRAGMA foreign_keys;").fetchone()[0]
    assert fk == 1


def test_schema_created_on_first_run(fresh_db):
    rows = fresh_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    tables = {r[0] for r in rows}
    assert {"runs", "versions", "citations", "logs"}.issubset(tables)


def test_get_cursor_and_commit_persist(fresh_db):
    cur = db.get_cursor()
    cur.execute(
        "INSERT INTO runs(topic, started_at) VALUES (?, datetime('now'))",
        ("t",),
    )
    db.commit()
    count = fresh_db.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    assert count == 1


def test_foreign_key_enforced(fresh_db):
    with pytest.raises(sqlite3.IntegrityError):
        cur = db.get_cursor()
        cur.execute(
            "INSERT INTO versions(run_id, step, body_markdown, created_at) VALUES (1,1,'',datetime('now'))"
        )
        db.commit()
