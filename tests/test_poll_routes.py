import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from agents.streaming import stream
from web.auth import verify_jwt

repo_src = Path(__file__).resolve().parents[1] / "src"
if str(repo_src) in sys.path:
    sys.path.remove(str(repo_src))

sys.path.insert(0, str(repo_src))


def reload_routes() -> None:
    spec = importlib.util.spec_from_file_location(
        "poll", repo_src / "web" / "routes" / "poll.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    globals()["poll_routes"] = module


poll_routes: Any = None
reload_routes()


def create_app() -> FastAPI:
    app = FastAPI()
    app.state.settings = SimpleNamespace()
    api = APIRouter(prefix="/api", dependencies=[Depends(verify_jwt)])
    api.include_router(poll_routes.router)
    app.include_router(api)
    app.dependency_overrides[verify_jwt] = lambda: {"role": "user"}
    return app


def test_poll_returns_latest_payload() -> None:
    client = TestClient(create_app())
    stream("updates", {"progress": 1})
    resp = client.get("/api/poll/updates")
    assert resp.status_code == 200
    assert resp.json()["payload"] == {"progress": 1}


def test_workspace_poll_returns_latest_payload() -> None:
    client = TestClient(create_app())
    stream("ws:values", {"status": "done"})
    resp = client.get("/api/poll/ws/values")
    assert resp.status_code == 200
    assert resp.json()["payload"] == {"status": "done"}


def test_poll_returns_204_when_empty() -> None:
    client = TestClient(create_app())
    resp = client.get("/api/poll/messages")
    assert resp.status_code == 204
