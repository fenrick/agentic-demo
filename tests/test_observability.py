"""Tests for the observability module's tracing toggles."""

from __future__ import annotations

import logging
import types

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
    monkeypatch.setattr("observability.install_auto_tracing", lambda: None)
    for name in [
        "instrument_pydantic",
        "instrument_httpx",
        "instrument_sqlalchemy",
        "instrument_sqlite3",
        "instrument_system_metrics",
    ]:
        monkeypatch.setattr(logfire, name, lambda *a, **k: None)
    monkeypatch.setattr(logfire, "loguru_handler", lambda: {"sink": None})
    monkeypatch.setattr(loguru_logger, "add", lambda *a, **k: None)
    init_observability()
    assert called is True


def test_loguru_and_logfire_handlers_aligned(monkeypatch):
    """Loguru sinks and standard logging handlers are replaced by Logfire."""

    monkeypatch.setenv("ENABLE_TRACING", "1")
    monkeypatch.setattr("observability.install_auto_tracing", lambda: None)
    for name in [
        "instrument_pydantic",
        "instrument_httpx",
        "instrument_sqlalchemy",
        "instrument_sqlite3",
        "instrument_system_metrics",
    ]:
        monkeypatch.setattr(logfire, name, lambda *a, **k: None)
    monkeypatch.setattr(logfire, "configure", lambda *a, **k: None)
    monkeypatch.setattr(logfire, "loguru_handler", lambda: {"sink": None})

    removed = []
    added = []

    def fake_remove(*_a, **_k):
        removed.append(True)

    def fake_add(*_a, **_k):
        added.append(True)

    monkeypatch.setattr(loguru_logger, "remove", fake_remove)
    monkeypatch.setattr(loguru_logger, "add", fake_add)

    class HandlerList(list):
        def clear(self):  # type: ignore[override]
            cleared.append(True)
            super().clear()

    cleared: list[bool] = []

    def add_handler(_):
        handlers_added.append(True)

    handlers_added: list[bool] = []
    root_logger = types.SimpleNamespace(handlers=HandlerList(), addHandler=add_handler)
    monkeypatch.setattr(logging, "getLogger", lambda: root_logger)

    init_observability()

    assert removed and added
    assert cleared and handlers_added
