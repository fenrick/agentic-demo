"""Unit tests for edge registration in the orchestrator."""

from __future__ import annotations

from pathlib import Path

from core.orchestrator import GraphOrchestrator


def dummy_cond(prev, state):
    return True


def cond_str(prev, state):
    return "loop"


def test_register_edges_coerces_boolean_keys():
    orchestrator = GraphOrchestrator(spec_path=Path("spec"))
    orchestrator._nodes = {}
    orchestrator._edge_spec = [
        {
            "source": "A",
            "condition": "tests.test_orchestrator_edges.dummy_cond",
            "mapping": {"True": "B", "False": "C"},
        }
    ]
    orchestrator.register_edges()
    mapping = orchestrator.graph.conditionals["A"][1]
    assert mapping[True] == "B"
    assert mapping[False] == "C"


def test_register_edges_preserves_non_boolean_keys():
    orchestrator = GraphOrchestrator(spec_path=Path("spec"))
    orchestrator._nodes = {}
    orchestrator._edge_spec = [
        {
            "source": "A",
            "condition": "tests.test_orchestrator_edges.cond_str",
            "mapping": {"loop": "B", "continue": "C"},
        }
    ]
    orchestrator.register_edges()
    mapping = orchestrator.graph.conditionals["A"][1]
    assert mapping["loop"] == "B"
    assert mapping["continue"] == "C"
