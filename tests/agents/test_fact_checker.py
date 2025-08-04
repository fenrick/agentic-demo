"""Tests for the fact checker agent."""

import asyncio
import pytest

from agents.fact_checker import (
    assess_hallucination_probabilities,
    run_fact_checker,
    scan_unsupported_claims,
    verify_sources,
)
from core.state import Outline, State


def test_assess_hallucination_probabilities_flags_low_confidence():
    text = "The sky is blue. Maybe unicorns exist."
    results = assess_hallucination_probabilities(text)
    assert len(results) == 1
    assert "unicorns" in results[0].sentence


def test_scan_unsupported_claims_detects_phrases():
    text = "Studies show that coffee increases productivity.\nThis is well known."
    flags = scan_unsupported_claims(text)
    assert len(flags) == 1
    assert flags[0].line_number == 1


def test_run_fact_checker_compiles_report():
    outline = Outline(
        steps=["Studies show coffee is great.", "Maybe unicorns exist."],
    )
    state = State(outline=outline)
    report = asyncio.run(run_fact_checker(state))
    assert report.hallucination_count == 1
    assert report.unsupported_claims_count == 1


def test_run_fact_checker_requires_steps():
    state = State(outline=Outline(steps=[]))
    with pytest.raises(ValueError):
        asyncio.run(run_fact_checker(state))


def test_verify_sources_marks_unchecked_when_offline(monkeypatch):
    monkeypatch.setenv("OFFLINE_MODE", "1")
    import config

    config._settings = None  # reset cached settings
    results = verify_sources(["https://example.com"])
    assert results[0].status == "unchecked"
