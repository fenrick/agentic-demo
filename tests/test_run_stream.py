import sqlite3
from pathlib import Path

import app.db as db
from app.api import app
from fastapi.testclient import TestClient


def test_run_streams_tokens_and_persists(tmp_path: Path) -> None:
    def override_conn() -> sqlite3.Connection:
        return db.connect(str(tmp_path / "runs.db"))

    app.dependency_overrides[db.connect] = override_conn
    client = TestClient(app)
    resp = client.post("/runs", json={"topic": "Testing"})
    run_id = resp.json()["run_id"]
    events: list[str] = []
    with client.stream("GET", f"/runs/{run_id}/stream") as r:
        for line in r.iter_lines():
            if line:
                events.append(line)
    token_events = [e for e in events if e.startswith("event: token")]
    log_events = [e for e in events if e.startswith("event: log")]
    assert token_events and log_events
    conn = override_conn()
    row = conn.execute(
        "SELECT topic, finished_at FROM runs WHERE id=?", (run_id,)
    ).fetchone()
    assert row[0] == "Testing" and row[1] is not None
