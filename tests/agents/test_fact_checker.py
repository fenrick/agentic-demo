"""Tests for the fact checker agent."""

import asyncio
from dataclasses import dataclass

from core.state import State
from agents.fact_checker import (
    assess_hallucination_probabilities,
    scan_unsupported_claims,
    run_fact_checker,
)


@dataclass(slots=True)
class Outline:
    markdown: str


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
    text = "Studies show coffee is great.\nMaybe unicorns exist."
    outline = Outline(markdown=text)
    state = State()
    state.outline = outline
    report = asyncio.run(run_fact_checker(state))
    assert report.hallucination_count == 1
    assert report.unsupported_claims_count == 1
