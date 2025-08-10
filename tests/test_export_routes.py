"""Tests for export API routes."""

import importlib
import importlib.util  # noqa: E402
import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from fastapi import APIRouter, Depends, FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from web.auth import verify_jwt  # noqa: E402

repo_src = Path(__file__).resolve().parents[1] / "src"
if str(repo_src) in sys.path:
    sys.path.remove(str(repo_src))

sys.path.insert(0, str(repo_src))


def reload_routes() -> None:
    """Load export routes module into ``export_routes``."""

    spec = importlib.util.spec_from_file_location(
        "export", repo_src / "web" / "routes" / "export.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    globals()["export_routes"] = module


export_routes: Any = None
reload_routes()


def create_app(tmp_path: Path, db_path: Path | None = None) -> FastAPI:
    """Create a FastAPI app with the export router."""

    app = FastAPI()
    app.state.settings = SimpleNamespace(data_dir=tmp_path)
    app.state.db_path = str(db_path or tmp_path / "lecture.db")
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


def test_download_routes_return_content(tmp_path: Path) -> None:
    """Export routes return non-empty Markdown, DOCX and PDF files."""

    for mod in [
        "docx",
        "docx.document",
        "weasyprint",
        "export.docx_exporter",
        "export.pdf_exporter",
        "web.api.export_endpoints",
    ]:
        sys.modules.pop(mod, None)
    import docx  # noqa: F401  # pylint: disable=unused-import
    import weasyprint  # noqa: F401  # pylint: disable=unused-import

    reload_routes()

    db_path = tmp_path / "lecture.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE lectures (workspace_id TEXT, lecture_json TEXT, created_at TEXT)"
    )
    lecture = {
        "title": "Demo",
        "learning_objectives": ["lo"],
        "activities": [{"type": "Lecture", "description": "desc", "duration_min": 5}],
        "duration_min": 5,
        "references": [
            {
                "url": "http://x",
                "title": "X",
                "retrieved_at": "2024-01-01",
            }
        ],
    }
    conn.execute(
        "INSERT INTO lectures VALUES (?,?,datetime('now'))",
        ("ws", json.dumps(lecture)),
    )
    conn.commit()
    conn.close()

    client = TestClient(create_app(tmp_path, db_path))

    md = client.get("/api/export/ws/md")
    assert md.status_code == 200
    assert md.text.strip()
    assert md.headers["cache-control"] == "no-store"
    assert "etag" in md.headers

    docx_resp = client.get("/api/export/ws/docx")
    assert docx_resp.status_code == 200
    assert docx_resp.content.startswith(b"PK")
    assert docx_resp.headers["cache-control"] == "no-store"
    assert "etag" in docx_resp.headers

    pdf = client.get("/api/export/ws/pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert pdf.headers["cache-control"] == "no-store"
    assert "etag" in pdf.headers
