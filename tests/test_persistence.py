import pytest

from app import persistence


@pytest.fixture
def conn(tmp_path):
    db = tmp_path / "test.db"
    connection = persistence.get_connection(str(db))
    persistence.init_db(connection)
    yield connection
    connection.close()


def test_wal_enabled(conn):
    mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
    assert mode == "wal"


def test_init_db_creates_tables(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    tables = {row[0] for row in rows}
    assert {"runs", "versions", "citations", "logs"}.issubset(tables)


def test_save_checkpoint_roundtrip(conn):
    v1 = persistence.save_checkpoint(conn, "run1", "a", ["c1"])
    v2 = persistence.save_checkpoint(conn, "run1", "b")
    assert (v1, v2) == (1, 2)
    rows = persistence.read_versions(conn, "run1")
    assert [r["data"] for r in rows] == ["a", "b"]
    c_rows = conn.execute("SELECT citation FROM citations").fetchall()
    assert [r[0] for r in c_rows] == ["c1"]


def test_read_versions_empty(conn):
    assert persistence.read_versions(conn, "missing") == []


def test_add_log_roundtrip(conn):
    persistence.add_log(conn, "run2", "INFO", "hi")
    rows = conn.execute("SELECT level, message FROM logs").fetchall()
    assert [(r[0], r[1]) for r in rows] == [("INFO", "hi")]
