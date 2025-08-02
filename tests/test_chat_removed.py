from fastapi.testclient import TestClient

from app.api import app


def test_chat_endpoint_removed():
    client = TestClient(app)
    resp = client.post("/chat", params={"input": "x", "run": "r"})
    assert resp.status_code == 404
