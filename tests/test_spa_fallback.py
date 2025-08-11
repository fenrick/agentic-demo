"""Tests for serving the frontend with history-fallback routing."""

from __future__ import annotations

import importlib
from pathlib import Path

from fastapi.testclient import TestClient

import web.main as main_module
from config import load_settings


def _build_dist(tmp_path: Path) -> Path:
    """Create a minimal frontend dist directory for tests."""

    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html></html>")
    return tmp_path


def test_history_fallback_serves_index(monkeypatch, tmp_path: Path) -> None:
    """Unknown paths should return the SPA's ``index.html``."""

    dist = _build_dist(tmp_path)
    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    load_settings.cache_clear()
    main = importlib.reload(main_module)

    client = TestClient(main.app)
    resp = client.get("/some/deep/link")

    assert resp.status_code == 200
    assert resp.text == "<html></html>"

    load_settings.cache_clear()


def test_api_paths_bypass_spa(monkeypatch, tmp_path: Path) -> None:
    """Routes under ``/api`` should not serve the SPA."""

    dist = _build_dist(tmp_path)
    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    load_settings.cache_clear()
    main = importlib.reload(main_module)

    client = TestClient(main.app)
    resp = client.get("/api/missing")

    assert resp.status_code == 404
    assert resp.json() == {"detail": "Not Found"}

    load_settings.cache_clear()
