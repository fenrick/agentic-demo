"""FastAPI application for agentic demo."""

from __future__ import annotations

import sqlite3
from collections.abc import AsyncIterator
from typing import cast

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import Response, StreamingResponse

from . import db
from .graph.builder import build_graph
from .graph.state import LectureState
from web.router import router as web_router

app = FastAPI()
app.include_router(web_router)

# TODO(#test_chat_endpoint_removed): ensure legacy /chat endpoint stays removed.


def _run_state(topic: str) -> LectureState:
    return {
        "topic": topic,
        "outline": "",
        "citations": [],
        "action_log": [],
        "stream_buffer": [],
    }


@app.post("/runs")
async def create_run(
    payload: dict, conn: sqlite3.Connection = Depends(db.connect)
) -> dict:
    """Start a new run and return its identifier."""

    topic = payload.get("topic", "")
    cur = conn.execute(
        "INSERT INTO runs(topic, started_at) VALUES (?, CURRENT_TIMESTAMP)",
        (topic,),
    )
    run_id = cast(int, cur.lastrowid)
    conn.commit()
    return {"run_id": run_id}


@app.get("/runs/{run_id}/stream")
async def stream_run(
    run_id: int, conn: sqlite3.Connection = Depends(db.connect)
) -> StreamingResponse:
    """Execute the lecture graph and stream logs and tokens."""

    cur = conn.execute("SELECT topic FROM runs WHERE id=?", (run_id,))
    row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")
    topic = row[0]
    graph = build_graph()

    async def event_gen() -> AsyncIterator[str]:
        state: LectureState = _run_state(topic)
        step = 0
        for event in graph.stream(state):
            step += 1
            name, delta = next(iter(event.items()))
            state.update(delta)
            body = state.get("outline") or "".join(state.get("stream_buffer", []))
            cur_v = conn.execute(
                "INSERT INTO versions(run_id, step, body_markdown, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (run_id, step, body),
            )
            version_id = cast(int, cur_v.lastrowid)
            for c in state.get("citations", []):
                conn.execute(
                    "INSERT INTO citations(version_id, url, snippet) VALUES (?, ?, ?)",
                    (version_id, c["url"], c["snippet"]),
                )
            log_msg = state.get("action_log", [])[-1] if state.get("action_log") else ""
            conn.execute(
                "INSERT INTO logs(run_id, agent, thought, result, created_at) VALUES (?,?,?,?, CURRENT_TIMESTAMP)",
                (run_id, name, log_msg, body),
            )
            conn.commit()
            yield f"event: log\ndata: {name}|{log_msg}\n\n"
            if name == "synth":
                for token in delta.get("stream_buffer", []):
                    yield f"event: token\ndata: {token}\n\n"
        conn.execute(
            "UPDATE runs SET finished_at=CURRENT_TIMESTAMP WHERE id=?",
            (run_id,),
        )
        conn.commit()
        yield "event: end\ndata: done\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.get("/runs/{run_id}/download/{fmt}")
def download_run(
    run_id: int, fmt: str, conn: sqlite3.Connection = Depends(db.connect)
) -> Response:
    """Download the final lecture in Markdown, DOCX or PDF."""

    cur = conn.execute(
        "SELECT body_markdown FROM versions WHERE run_id=? ORDER BY step DESC LIMIT 1",
        (run_id,),
    )
    row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")
    body = row[0]
    if fmt == "md":
        return Response(body, media_type="text/markdown")
    if fmt == "docx":
        from docx import Document  # type: ignore
        from io import BytesIO

        buf = BytesIO()
        doc = Document()
        doc.add_paragraph(body)
        doc.save(buf)
        return Response(
            buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    if fmt == "pdf":
        from fpdf import FPDF  # type: ignore

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in body.splitlines():
            pdf.multi_cell(0, 10, line)
        return Response(
            pdf.output(dest="S").encode("latin1"),
            media_type="application/pdf",
        )
    raise HTTPException(status_code=400, detail="unsupported format")
