"""Persistence layer for tracking runs and versions.

Defines the schema for four tables:
* ``runs`` - high level run metadata.
* ``versions`` - checkpointed states for a run.
* ``citations`` - references attached to a version.
* ``logs`` - textual log lines for a run.

The module exposes helper functions for interacting with the database:
* :func:`get_connection` creates a SQLite connection with WAL enabled.
* :func:`init_db` sets up the tables.
* :func:`save_checkpoint` stores a new version for a run.
* :func:`read_versions` retrieves historical versions for a run.

The implementation intentionally keeps a lightweight surface area.  New
features should continue to follow TDD discipline by adding tests for
any TODO references below.
"""

from __future__ import annotations

import sqlite3
from typing import Sequence, cast

# TODO(#test_save_checkpoint_roundtrip): support bulk citation metadata
# beyond simple strings.
# TODO(#test_read_versions_empty): add pagination for large histories.
# TODO(#test_wal_enabled): expose an option to disable WAL for in-memory
# databases when concurrency is not required.


def get_connection(path: str = ":memory:") -> sqlite3.Connection:
    """Return a SQLite connection with WAL journal mode.

    Parameters
    ----------
    path:
        Filesystem path to the database. ``":memory:"`` creates an
        in-memory database.

    Returns
    -------
    sqlite3.Connection
        Configured connection with ``row_factory`` set to ``sqlite3.Row``
        and write-ahead logging (WAL) enabled.
    """

    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    version INTEGER NOT NULL,
    data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(run_id, version)
);

CREATE TABLE IF NOT EXISTS citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL REFERENCES versions(id),
    citation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db(conn: sqlite3.Connection) -> None:
    """Create the required tables if they do not already exist.

    Parameters
    ----------
    conn:
        Open connection returned by :func:`get_connection`.
    """

    conn.executescript(SCHEMA)
    conn.commit()


def _ensure_run(conn: sqlite3.Connection, name: str) -> int:
    """Return the run identifier for ``name`` creating a row if needed."""

    row = conn.execute("SELECT id FROM runs WHERE name = ?", (name,)).fetchone()
    if row:
        return int(row["id"])
    cur = conn.execute("INSERT INTO runs(name) VALUES (?)", (name,))
    return cast(int, cur.lastrowid)


def _next_version(conn: sqlite3.Connection, run_id: int) -> int:
    """Return the next sequential version for a run."""

    cur = conn.execute(
        "SELECT COALESCE(MAX(version), 0) + 1 FROM versions WHERE run_id = ?",
        (run_id,),
    )
    return int(cur.fetchone()[0])


def save_checkpoint(
    conn: sqlite3.Connection,
    run_name: str,
    data: str,
    citations: Sequence[str] | None = None,
) -> int:
    """Persist ``data`` as the next version for ``run_name``.

    Parameters
    ----------
    conn:
        Active database connection.
    run_name:
        Identifier for the logical run.
    data:
        Arbitrary JSON or text blob representing the checkpoint.
    citations:
        Optional sequence of citation strings associated with the
        checkpoint.

    Returns
    -------
    int
        The version number assigned to the checkpoint.
    """

    run_id = _ensure_run(conn, run_name)
    version = _next_version(conn, run_id)
    cur = conn.execute(
        "INSERT INTO versions(run_id, version, data) VALUES (?, ?, ?)",
        (run_id, version, data),
    )
    version_id = cast(int, cur.lastrowid)
    if citations:
        conn.executemany(
            "INSERT INTO citations(version_id, citation) VALUES (?, ?)",
            [(version_id, c) for c in citations],
        )
    conn.commit()
    return version


def read_versions(conn: sqlite3.Connection, run_name: str) -> list[sqlite3.Row]:
    """Return historical versions for ``run_name`` in ascending order.

    Parameters
    ----------
    conn:
        Active database connection.
    run_name:
        Identifier for the logical run.

    Returns
    -------
    list[sqlite3.Row]
        List of ``Row`` objects each containing ``version`` and ``data``.
        Returns an empty list if the run does not exist.
    """

    row = conn.execute("SELECT id FROM runs WHERE name = ?", (run_name,)).fetchone()
    if not row:
        return []
    run_id = int(row["id"])
    cur = conn.execute(
        "SELECT version, data FROM versions WHERE run_id = ? ORDER BY version",
        (run_id,),
    )
    return list(cur.fetchall())


def add_log(conn: sqlite3.Connection, run_name: str, level: str, message: str) -> None:
    """Append a log entry for ``run_name``.

    Parameters
    ----------
    conn:
        Active database connection.
    run_name:
        Name of the run receiving the log line.
    level:
        Logging level such as ``"INFO"``.
    message:
        Body of the log message.
    """

    run_id = _ensure_run(conn, run_name)
    conn.execute(
        "INSERT INTO logs(run_id, level, message) VALUES (?, ?, ?)",
        (run_id, level, message),
    )
    conn.commit()


# TODO(#test_add_log_roundtrip): surface a dedicated API for querying logs.
