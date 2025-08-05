"""Tests for the data entry API endpoints."""

from pathlib import Path
import sys

repo_src = Path(__file__).resolve().parents[1] / "src"
if str(repo_src) in sys.path:
    sys.path.remove(str(repo_src))
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

sys.path.insert(0, str(repo_src))

import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "entries", repo_src / "web" / "routes" / "entries.py"
)
assert spec and spec.loader
entries_routes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entries_routes)


def create_app() -> FastAPI:
    """Create a FastAPI app with the entries router."""

    app = FastAPI()
    app.include_router(entries_routes.router)
    return app


def test_create_and_list_entries() -> None:
    """Ensure entries can be created and retrieved."""

    entries_routes._entries.clear()
    client = TestClient(create_app())
    resp = client.post("/entries", json={"name": "Alice", "email": "alice@example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Alice"
    resp = client.get("/entries")
    assert resp.status_code == 200
    entries = resp.json()
    assert entries[0]["email"] == "alice@example.com"
