from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from unittest.mock import patch
import json
import pytest
import web.router as web_router
from web.router import _to_docx_bytes, Document

from app.api import app


def test_websocket_streaming_basic():
    client = TestClient(app)
    with (
        patch("web.router.plan", return_value="p"),
        patch("web.router.research", return_value="r"),
        patch("web.router.draft", return_value="d"),
        patch("web.router.review", return_value="done"),
    ):
        with client.websocket_connect("/stream?input=x&mode=basic") as ws:
            assert ws.receive_text() == "p"
            assert ws.receive_text() == "r"
            assert ws.receive_text() == "d"
            assert ws.receive_text() == "done"
            with pytest.raises(WebSocketDisconnect):
                ws.receive_text()


def test_export_docx():
    client = TestClient(app)
    with patch("web.router._to_docx_bytes", return_value=b"doc") as mock_fn:
        resp = client.post("/export/docx", json={"text": "hi"})
    assert resp.status_code == 200
    mock_fn.assert_called_once_with("hi")
    assert resp.headers["Content-Disposition"].startswith("attachment")
    assert resp.content == b"doc"


def test_ui_includes_cancel_and_error_handlers():
    """UI should contain cancel button and websocket error handling."""
    client = TestClient(app)
    resp = client.get("/ui")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="cancel"' in html  # cancel button
    assert ".onerror" in html  # websocket error handler
    assert "catch" in html  # fetch error handling


# TODO: ensure /export/docx falls back to plain text if Document is missing
def test_export_docx_without_document(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("web.router.Document", None)
    resp = client.post("/export/docx", json={"text": "hi"})
    assert resp.status_code == 200
    assert resp.content == b"hi"


def test_websocket_streaming_overlay_dict():
    """Overlay mode should stringify dict results for websocket transmission."""
    client = TestClient(app)
    overlay_output = {"slides": []}
    with (
        patch("web.router.plan", return_value="p"),
        patch("web.router.research", return_value="r"),
        patch("web.router.draft", return_value="d"),
        patch("web.router.review", return_value="done"),
        patch.object(web_router.OverlayAgent, "__call__", return_value=overlay_output),
    ):
        with client.websocket_connect("/stream?input=x&mode=overlay") as ws:
            assert ws.receive_text() == "p"
            assert ws.receive_text() == "r"
            assert ws.receive_text() == "d"
            assert ws.receive_text() == "done"
            assert ws.receive_text() == json.dumps(overlay_output)
            with pytest.raises(WebSocketDisconnect):
                ws.receive_text()


def test_to_docx_bytes_generates_zip():
    """Ensure generated DOCX bytes have zip file header when Document is available."""
    if Document is None:
        pytest.skip("python-docx not installed")
    data = _to_docx_bytes("hi")
    assert data.startswith(b"PK")
