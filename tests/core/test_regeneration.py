"""Tests for selective content regeneration logic."""

import core.regenerator as regen
from core.state import State
from models.critique_report import (ActivityDiversityReport,
                                    BloomCoverageReport, CognitiveLoadReport,
                                    CritiqueReport)
from models.fact_check_report import (ClaimFlag, FactCheckReport,
                                      SentenceProbability)


def build_critique_report() -> CritiqueReport:
    bloom = BloomCoverageReport(level_counts={}, missing_levels=[], coverage_score=1.0)
    diversity = ActivityDiversityReport(type_percentages={}, is_balanced=True)
    cognitive = CognitiveLoadReport(total_duration=0, overloaded_segments=["A"])
    return CritiqueReport(bloom=bloom, diversity=diversity, cognitive_load=cognitive)


def test_get_sections_to_regenerate_handles_reports():
    critique = build_critique_report()
    assert regen.get_sections_to_regenerate(critique) == ["A"]

    fact_report = FactCheckReport(
        hallucinations=[
            SentenceProbability(line_number=1, sentence="a", probability=0.2)
        ],
        unsupported_claims=[ClaimFlag(line_number=2, snippet="b")],
    )
    assert regen.get_sections_to_regenerate(fact_report) == ["1", "2"]


def test_orchestrate_regeneration_invokes_and_counts(monkeypatch):
    report = FactCheckReport(
        hallucinations=[
            SentenceProbability(line_number=1, sentence="a", probability=0.1)
        ],
        unsupported_claims=[ClaimFlag(line_number=2, snippet="b")],
    )
    state = State()
    captured: list[list[str]] = []

    def fake_apply(graph, st, sections):
        captured.append(list(sections))

    monkeypatch.setattr(regen, "apply_regeneration", fake_apply)
    regen.orchestrate_regeneration(state, report, graph=object())
    assert captured == [["1", "2"]]
    assert state.retry_counts == {"1": 1, "2": 1}


def test_orchestrate_regeneration_stops_after_three_attempts(monkeypatch):
    report = FactCheckReport(
        hallucinations=[
            SentenceProbability(line_number=1, sentence="a", probability=0.1)
        ]
    )
    state = State()
    calls: list[list[str]] = []

    def fake_apply(graph, st, sections):
        calls.append(list(sections))

    monkeypatch.setattr(regen, "apply_regeneration", fake_apply)
    dummy_graph = object()
    for _ in range(4):
        regen.orchestrate_regeneration(state, report, graph=dummy_graph)
    assert len(calls) == 3
    assert state.retry_counts["1"] == 3
