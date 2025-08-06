"""Tests for citation API routes."""

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
    "citation", repo_src / "web" / "routes" / "citation.py"
)
assert spec and spec.loader
citation_routes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(citation_routes)


def create_app() -> FastAPI:
    """Create a FastAPI app with the citation router."""

    app = FastAPI()
    app.include_router(citation_routes.router)
    return app


def test_list_and_get_citation() -> None:
    """Ensure citation routes respond with placeholders."""

    client = TestClient(create_app())
    resp = client.get("/workspaces/abc/citations")
    assert resp.status_code == 200
    assert resp.json() == []

    resp = client.get("/workspaces/abc/citations/123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["url"].endswith("/123")
    assert data["title"] == "Placeholder"
