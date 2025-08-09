"""Tests for the data entry API endpoints."""

import importlib.util  # noqa: E402
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from web.auth import verify_jwt  # noqa: E402

repo_src = Path(__file__).resolve().parents[1] / "src"
if str(repo_src) in sys.path:
    sys.path.remove(str(repo_src))

sys.path.insert(0, str(repo_src))


spec = importlib.util.spec_from_file_location(
    "entries", repo_src / "web" / "routes" / "entries.py"
)
assert spec and spec.loader
entries_routes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entries_routes)


def create_app() -> FastAPI:
    """Create a FastAPI app with the entries router."""

    app = FastAPI()
    api = APIRouter(prefix="/api", dependencies=[Depends(verify_jwt)])
    api.include_router(entries_routes.router)
    app.include_router(api)
    app.dependency_overrides[verify_jwt] = lambda: {"role": "user"}
    return app


def test_create_and_list_entries() -> None:
    """Ensure entries can be created and retrieved."""

    entries_routes._entries.clear()
    client = TestClient(create_app())
    resp = client.post("/api/entries", json={"topic": "Graph Theory"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["topic"] == "Graph Theory"
    resp = client.get("/api/entries")
    assert resp.status_code == 200
    entries = resp.json()
    assert entries[0]["topic"] == "Graph Theory"
