import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from web.api.export_endpoints import register_export_routes


def _setup_db(path: Path) -> Path:
    db_path = path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE lectures (workspace_id TEXT, lecture_json TEXT, created_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE citations (workspace_id TEXT, url TEXT, title TEXT, retrieved_at TEXT, licence TEXT)"
    )
    lecture = {
        "title": "Intro to AI",
        "author": "Alice",
        "date": "2024-01-01",
        "version": "1.0",
        "summary": "Basics of AI",
        "tags": ["ai", "intro"],
        "prerequisites": ["Python"],
        "duration_min": 60,
        "learning_objectives": ["Understand basics"],
        "activities": [
            {
                "type": "Lecture",
                "description": "Overview",
                "duration_min": 30,
                "learning_objectives": ["Understand basics"],
            }
        ],
        "slide_bullets": [{"slide_number": 1, "bullets": ["What is AI?", "History"]}],
        "speaker_notes": "Engage audience",
        "assessment": [{"type": "Quiz", "description": "Check", "max_score": 10}],
        "references": [
            {
                "url": "http://example.com",
                "title": "Example",
                "retrieved_at": "2024-01-01",
                "licence": "CC",
            }
        ],
    }
    conn.execute(
        "INSERT INTO lectures VALUES (?,?,?)",
        ("ws1", json.dumps(lecture), "2024-01-01"),
    )
    conn.execute(
        "INSERT INTO citations VALUES (?,?,?,?,?)",
        ("ws1", "http://example.com", "Example", "2024-01-01", "CC"),
    )
    conn.commit()
    conn.close()
    return db_path


def _create_client(db_path: str) -> TestClient:
    app = FastAPI()
    app.state.db_path = db_path
    register_export_routes(app)
    return TestClient(app)


def test_markdown_route_returns_200_and_markdown(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    client = _create_client(str(db))
    res = client.get("/export/ws1/md")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/markdown")
    assert "title: Intro to AI" in res.text


def test_docx_route_returns_correct_content_type(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    client = _create_client(str(db))
    res = client.get("/export/ws1/docx")
    assert res.status_code == 200
    assert (
        res.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert len(res.content) > 0


def test_pdf_route_returns_pdf(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    client = _create_client(str(db))
    res = client.get("/export/ws1/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 0


def test_citations_route_returns_valid_json(tmp_path: Path) -> None:
    db = _setup_db(tmp_path)
    client = _create_client(str(db))
    res = client.get("/export/ws1/citations.json")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/json"
    data = json.loads(res.content.decode("utf-8"))
    assert data[0]["url"] == "http://example.com"


def test_all_route_returns_zip_with_files(tmp_path: Path) -> None:
    from zipfile import ZipFile
    import io

    db = _setup_db(tmp_path)
    client = _create_client(str(db))
    res = client.get("/export/ws1/all")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    zf = ZipFile(io.BytesIO(res.content))
    names = set(zf.namelist())
    assert {"lecture.md", "lecture.docx", "lecture.pdf", "citations.json"}.issubset(
        names
    )
