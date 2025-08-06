"""Tests for export API routes."""

from pathlib import Path
import sys
from types import SimpleNamespace

repo_src = Path(__file__).resolve().parents[1] / "src"
if str(repo_src) in sys.path:
    sys.path.remove(str(repo_src))
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

sys.path.insert(0, str(repo_src))

import importlib.util  # noqa: E402

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
    app.include_router(export_routes.router)
    return app


def test_export_status_and_urls(tmp_path: Path) -> None:
    """Ensure status and URL routes respond correctly."""

    client = TestClient(create_app(tmp_path))

    resp = client.get("/workspaces/ws/export/status")
    assert resp.status_code == 200
    assert resp.json() == {"ready": False}

    export_dir = tmp_path / "exports" / "ws"
    export_dir.mkdir(parents=True)
    (export_dir / "lecture.md").write_text("x")
    (export_dir / "lecture.docx").write_bytes(b"x")
    (export_dir / "lecture.pdf").write_bytes(b"x")

    resp = client.get("/workspaces/ws/export/status")
    assert resp.status_code == 200
    assert resp.json() == {"ready": True}

    resp = client.get("/workspaces/ws/export/urls")
    assert resp.status_code == 200
    assert resp.json() == {
        "md": "/export/ws/md",
        "docx": "/export/ws/docx",
        "pdf": "/export/ws/pdf",
        "zip": "/export/ws/all",
    }
