from fastapi.testclient import TestClient
from unittest.mock import patch

from app.api import app
from app.agents import ChatAgent


def test_chat_endpoint():
    client = TestClient(app)

    async def fake_arun(_: str) -> dict:
        return {"messages": [], "output": "ok"}

    with (
        patch.object(ChatAgent, "__call__", return_value="ok"),
        patch("app.agents.perplexity.search", return_value="r"),
        patch("app.api.flow.arun", fake_arun),
    ):
        response = client.post("/chat", params={"input": "topic", "run": "r"})
    assert response.status_code == 200
    data = response.json()
    assert data == {"response": "ok"}


def test_mcp_endpoint():
    client = TestClient(app)
    with patch("app.api.mcp.edit", return_value="doc") as edit:
        resp = client.post("/mcp", json={"addition": "add"})
    assert resp.status_code == 200
    assert resp.json() == {"text": "doc"}
    edit.assert_called_once_with("add")


def test_chat_persists_steps(monkeypatch):
    """Each agent step is persisted and logged."""
    steps = ["a", "b"]

    async def fake_arun(_: str) -> dict:
        return {"messages": steps, "output": "b"}

    records: list[tuple[str, str]] = []

    def fake_save(conn, run, data, citations=None):  # type: ignore[unused-arg]
        records.append(("save", data))

    def fake_log(conn, run, level, message):  # type: ignore[unused-arg]
        records.append(("log", message))

    import app.api as api

    monkeypatch.setattr(api.flow, "arun", fake_arun)
    monkeypatch.setattr(api, "save_checkpoint", fake_save)
    monkeypatch.setattr(api, "add_log", fake_log)

    client = TestClient(app)
    resp = client.post("/chat", params={"input": "i", "run": "r"})
    assert resp.status_code == 200
    assert records == [
        ("save", "a"),
        ("log", "a"),
        ("save", "b"),
        ("log", "b"),
    ]


def test_versions_endpoint_returns_saved_versions(monkeypatch):
    """``GET /versions`` exposes stored checkpoints."""

    async def fake_arun(_: str) -> dict:
        return {"messages": ["s1", "s2"], "output": "s2"}

    # fresh database for the test
    from app.persistence import get_connection, init_db
    import app.api as api

    conn = get_connection()
    init_db(conn)
    monkeypatch.setattr(api, "conn", conn)
    monkeypatch.setattr(api.flow, "arun", fake_arun)

    client = TestClient(app)
    resp = client.post("/chat", params={"input": "i", "run": "run"})
    assert resp.status_code == 200

    resp = client.get("/versions", params={"run": "run"})
    assert resp.status_code == 200
    assert resp.json() == {
        "versions": [
            {"version": 1, "data": "s1"},
            {"version": 2, "data": "s2"},
        ]
    }
