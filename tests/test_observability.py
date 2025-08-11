"""Tests for the observability module's tracing toggles."""

from __future__ import annotations

import logfire
from loguru import logger as loguru_logger

from observability import init_observability


def test_init_observability_disabled(monkeypatch):
    """Tracing is skipped when ENABLE_TRACING is false."""

    called = False

    def fake_configure(*args, **kwargs):  # pragma: no cover - patched
        nonlocal called
        called = True

    monkeypatch.setenv("ENABLE_TRACING", "0")
    monkeypatch.setattr(logfire, "configure", fake_configure)
    init_observability()
    assert called is False


def test_init_observability_enabled(monkeypatch):
    """Tracing is configured when ENABLE_TRACING is true."""

    called = False

    def fake_configure(*args, **kwargs):  # pragma: no cover - patched
        nonlocal called
        called = True

    monkeypatch.setenv("ENABLE_TRACING", "1")
    monkeypatch.setattr(logfire, "configure", fake_configure)
    for name in [
        "instrument_pydantic",
        "instrument_httpx",
        "instrument_sqlalchemy",
        "instrument_sqlite3",
        "instrument_system_metrics",
    ]:
        monkeypatch.setattr(logfire, name, lambda *a, **k: None)
    monkeypatch.setattr(logfire, "loguru_handler", lambda: None)
    monkeypatch.setattr(loguru_logger, "add", lambda *a, **k: None)
    init_observability()
    assert called is True
