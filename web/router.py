"""Web UI routes and websocket streaming for agentic demo."""

from __future__ import annotations

from io import BytesIO
from typing import AsyncIterator, cast
import json
import pathlib

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import HTMLResponse

from app.graph import build_graph, GraphState
from app.overlay_agent import OverlayAgent

try:
    from docx import Document
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    Document = None  # type: ignore

router = APIRouter()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _run_stream(text: str, mode: str) -> AsyncIterator[str]:
    """Yield outputs from the conversation graph step by step."""
    overlay = OverlayAgent() if mode == "overlay" else None
    flow = build_graph(overlay, mode=mode)

    async def _inner() -> AsyncIterator[str]:
        state: GraphState = {
            "text": text,
            "draft": "",
            "approved": False,
            "history": [],
            "loops": 0,
        }
        async for event in flow.graph.astream(state):
            node, data = next(iter(event.items()))
            output = data["text"]
            if node == "overlay" and isinstance(output, dict):
                yield json.dumps(output)
            else:
                yield cast(str, output)

    return _inner()


def _to_docx_bytes(text: str) -> bytes:
    """Convert plain text to a DOCX binary."""
    if Document is None:  # pragma: no cover - dependency optional
        return text.encode()
    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# routes
# ---------------------------------------------------------------------------


@router.get("/ui")
async def ui() -> HTMLResponse:
    """Serve the demo HTML page."""
    html = (pathlib.Path(__file__).with_name("templates") / "ui.html").read_text()
    return HTMLResponse(html)


@router.websocket("/stream")
async def stream(websocket: WebSocket, input: str, mode: str = "basic") -> None:
    """Stream conversation results over a websocket."""
    await websocket.accept()
    try:
        async for msg in _run_stream(input, mode):
            await websocket.send_text(msg)
    except WebSocketDisconnect:  # pragma: no cover - client closed early
        pass
    finally:
        await websocket.close()


@router.post("/export/docx")
async def export_docx(payload: dict) -> Response:
    """Return DOCX file for provided text."""
    text = payload.get("text", "")
    data = _to_docx_bytes(text)
    headers = {"Content-Disposition": "attachment; filename=output.docx"}
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )
