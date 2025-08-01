from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from typing import AsyncIterator
from unittest.mock import patch
import json
import pytest
from web.router import _to_docx_bytes, Document

from app.api import app


def _fake_graph(events: list[tuple[str, str | dict]]) -> object:
    """Return an object mimicking a compiled graph for testing."""

    class DummyGraph:
        async def astream(self, _state: dict) -> AsyncIterator[dict]:
            for name, text in events:
                yield {name: {"text": text}}

    class Wrapper:
        def __init__(self) -> None:
            self.graph = DummyGraph()

    return Wrapper()


def test_websocket_streaming_basic():
    """stream endpoint should yield graph outputs sequentially."""
    client = TestClient(app)
    events = [
        ("plan", "p"),
        ("research", "r"),
        ("draft", "d"),
        ("review", "done"),
    ]
    with patch("web.router.build_graph", return_value=_fake_graph(events)):
        with client.websocket_connect("/stream?input=x&mode=basic") as ws:
            for expected in ["p", "r", "d", "done"]:
                assert ws.receive_text() == expected
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
    events = [
        ("plan", "p"),
        ("research", "r"),
        ("draft", "d"),
        ("review", "done"),
        ("overlay", overlay_output),
    ]
    with patch("web.router.build_graph", return_value=_fake_graph(events)):
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


def test_websocket_streaming_overlay_mixed_types():
    """OverlayAgent results of varying types should be sent correctly."""
    # TODO: ensure overlay outputs send raw strings and JSON for dicts
    client = TestClient(app)
    outputs = ["image", {"slides": [1]}]
    base_events = [
        ("plan", "p"),
        ("research", "r"),
        ("draft", "d"),
        ("review", "done"),
    ]
    for output in outputs:
        events = base_events + [("overlay", output)]
        with patch("web.router.build_graph", return_value=_fake_graph(events)):
            with client.websocket_connect("/stream?input=x&mode=overlay") as ws:
                for expected in [
                    "p",
                    "r",
                    "d",
                    "done",
                    json.dumps(output) if isinstance(output, dict) else output,
                ]:
                    assert ws.receive_text() == expected
                with pytest.raises(WebSocketDisconnect):
                    ws.receive_text()
