"""Authentication path tests."""

from __future__ import annotations

import os

import jwt
from fastapi.testclient import TestClient

from web.main import create_app


def test_missing_token_returns_401() -> None:
    """Requests without a JWT should be rejected."""
    client = TestClient(create_app())
    resp = client.get("/api/entries")
    assert resp.status_code == 401


def test_invalid_role_returns_403() -> None:
    """Tokens with insufficient role should be forbidden."""
    token = jwt.encode({"role": "guest"}, os.environ["JWT_SECRET"], algorithm="HS256")
    client = TestClient(create_app())
    resp = client.get("/api/entries", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
