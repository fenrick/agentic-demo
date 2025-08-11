"""Security middleware integration tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from config import load_settings
from web.main import create_app


def _new_client() -> TestClient:
    load_settings.cache_clear()
    return TestClient(create_app())


def test_security_headers_present() -> None:
    client = _new_client()
    response = client.get("/healthz")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == "geolocation=()"


def test_cors_default_allows_localhost(monkeypatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    client = _new_client()
    response = client.options(
        "/healthz",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_respects_configured_origins(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", '["https://example.com"]')
    client = _new_client()
    response = client.options(
        "/healthz",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers["access-control-allow-origin"] == "https://example.com"
