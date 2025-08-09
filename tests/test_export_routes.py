"""Tests for export API routes."""

import importlib.util  # noqa: E402
import sys
from pathlib import Path
from types import SimpleNamespace

from fastapi import APIRouter, Depends, FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from web.auth import verify_jwt  # noqa: E402

repo_src = Path(__file__).resolve().parents[1] / "src"
if str(repo_src) in sys.path:
    sys.path.remove(str(repo_src))

sys.path.insert(0, str(repo_src))


spec = importlib.util.spec_from_file_location(
    "export", repo_src / "web" / "routes" / "export.py"
)
assert spec and spec.loader
export_routes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export_routes)


def create_app(tmp_path: Path) -> FastAPI:
    """Create a FastAPI app with the export router."""

    app = FastAPI()
    app.state.settings = SimpleNamespace(data_dir=tmp_path)
    api = APIRouter(prefix="/api", dependencies=[Depends(verify_jwt)])
    api.include_router(export_routes.router)
    app.include_router(api)
    app.dependency_overrides[verify_jwt] = lambda: {"role": "user"}
    return app


def test_export_status_and_urls(tmp_path: Path) -> None:
    """Ensure status and URL routes respond correctly."""

    client = TestClient(create_app(tmp_path))

    resp = client.get("/api/workspaces/ws/export/status")
    assert resp.status_code == 200
    assert resp.json() == {"ready": False}

    export_dir = tmp_path / "exports" / "ws"
    export_dir.mkdir(parents=True)
    (export_dir / "lecture.md").write_text("x")
    (export_dir / "lecture.docx").write_bytes(b"x")
    (export_dir / "lecture.pdf").write_bytes(b"x")

    resp = client.get("/api/workspaces/ws/export/status")
    assert resp.status_code == 200
    assert resp.json() == {"ready": True}

    resp = client.get("/api/workspaces/ws/export/urls")
    assert resp.status_code == 200
    assert resp.json() == {
        "md": "/export/ws/md",
        "docx": "/export/ws/docx",
        "pdf": "/export/ws/pdf",
        "zip": "/export/ws/all",
    }
