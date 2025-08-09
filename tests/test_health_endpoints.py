"""Tests for health and readiness endpoints."""

import importlib.util  # noqa: E402
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

repo_src = Path(__file__).resolve().parents[1] / "src"
if str(repo_src) in sys.path:
    sys.path.remove(str(repo_src))

sys.path.insert(0, str(repo_src))

spec = importlib.util.spec_from_file_location(
    "health_endpoint", repo_src / "web" / "health_endpoint.py"
)
assert spec and spec.loader
health_endpoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(health_endpoint)


@asynccontextmanager
async def dummy_db():
    class Conn:
        async def execute(self, *_a, **_k):
            return None

    yield Conn()


def create_app() -> FastAPI:
    """Create a FastAPI app with health routes."""

    app = FastAPI()
    app.state.db = dummy_db
    app.state.research_client = object()
    app.add_api_route("/healthz", health_endpoint.healthz, methods=["GET"])
    app.add_api_route("/readyz", health_endpoint.readyz, methods=["GET"])
    return app


def test_health_and_ready() -> None:
    """Ensure health and readiness endpoints succeed."""

    client = TestClient(create_app())

    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    resp = client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}
