"""Tests for control API routes."""

import importlib.util  # noqa: E402
import sys
from pathlib import Path

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

repo_src = Path(__file__).resolve().parents[1] / "src"
if str(repo_src) in sys.path:
    sys.path.remove(str(repo_src))

sys.path.insert(0, str(repo_src))


spec = importlib.util.spec_from_file_location(
    "control", repo_src / "web" / "routes" / "control.py"
)
assert spec and spec.loader
control_routes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control_routes)


def create_app() -> FastAPI:
    """Create a FastAPI app with the control router."""

    class DummyGraph:
        async def run(self, _state):
            return _state

    app = FastAPI()
    app.state.graph = DummyGraph()
    app.include_router(control_routes.router)
    return app


def test_control_endpoints() -> None:
    """Ensure control routes respond with placeholders."""

    client = TestClient(create_app())

    resp = client.post("/workspaces/abc/run", json={"topic": "unit"})
    assert resp.status_code == 201
    assert resp.json() == {"job_id": "abc", "workspace_id": "abc"}

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
