from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

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
            with pytest.raises(RuntimeError):
                ws.receive_text()


def test_export_docx():
    client = TestClient(app)
    with patch("web.router._to_docx_bytes", return_value=b"doc") as mock_fn:
        resp = client.post("/export/docx", json={"text": "hi"})
    assert resp.status_code == 200
    mock_fn.assert_called_once_with("hi")
    assert resp.headers["Content-Disposition"].startswith("attachment")
    assert resp.content == b"doc"
