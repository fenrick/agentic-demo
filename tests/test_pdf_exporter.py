"""Tests for PDF export utilities."""

from __future__ import annotations

import sys

import pytest

from export.pdf_exporter import PdfExporter


def test_render_pdf_requires_weasyprint(monkeypatch: pytest.MonkeyPatch) -> None:
    """It raises a helpful error when WeasyPrint is unavailable."""

    monkeypatch.delitem(sys.modules, "weasyprint", raising=False)
    exporter = PdfExporter(":memory:")
    with pytest.raises(RuntimeError) as excinfo:
        exporter.render_pdf("<html><head></head><body></body></html>")
    assert "WeasyPrint" in str(excinfo.value)
