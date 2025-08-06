"""Tests for control API routes."""

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
    "control", repo_src / "web" / "routes" / "control.py"
)
assert spec and spec.loader
control_routes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control_routes)


def create_app() -> FastAPI:
    """Create a FastAPI app with the control router."""

    app = FastAPI()
    app.include_router(control_routes.router)
    return app


def test_control_endpoints() -> None:
    """Ensure control routes respond with placeholders."""

    client = TestClient(create_app())

    resp = client.post("/workspaces/abc/run", json={"topic": "unit"})
    assert resp.status_code == 201
    assert "job_id" in resp.json()

    resp = client.post("/workspaces/abc/pause")
    assert resp.status_code == 200
    assert resp.json() == {"workspace_id": "abc", "status": "paused"}

    resp = client.post("/workspaces/abc/retry")
    assert resp.status_code == 200
    assert resp.json() == {"workspace_id": "abc", "status": "retried"}

    resp = client.post("/workspaces/abc/resume")
    assert resp.status_code == 200
    assert resp.json() == {"workspace_id": "abc", "status": "resumed"}

    resp = client.post("/workspaces/abc/model", json={"model": "gpt"})
    assert resp.status_code == 200
    assert resp.json() == {"workspace_id": "abc", "model": "gpt"}
