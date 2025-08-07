"""Unit tests for edge registration in the orchestrator."""

# mypy: ignore-errors
from __future__ import annotations

import sys
import types
from pathlib import Path

# Stub modules required by core.orchestrator import

tiktoken_stub = types.ModuleType("tiktoken")
tiktoken_stub.encoding_for_model = lambda _name: types.SimpleNamespace(
    encode=lambda s: []
)
tiktoken_stub.get_encoding = lambda _name: types.SimpleNamespace(encode=lambda s: [])
sys.modules["tiktoken"] = tiktoken_stub

config_stub = types.ModuleType("config")


class _Settings:
    model = "openai:gpt"
    data_dir = Path(".")


config_stub.MODEL = "openai:gpt"
config_stub.DEFAULT_MODEL_NAME = "gpt"
config_stub.load_settings = lambda: _Settings()
sys.modules["config"] = config_stub

langgraph_graph_stub = types.ModuleType("langgraph.graph")


class _DummyStateGraph:
    def __init__(self, _state_type):
        pass

    def add_node(self, *_args, **_kwargs):
        pass

    def add_edge(self, *_args, **_kwargs):
        pass

    def add_conditional_edges(self, *_args, **_kwargs):
        pass

    def compile(self):
        return self


langgraph_graph_stub.END = "END"
langgraph_graph_stub.START = "START"
langgraph_graph_stub.StateGraph = _DummyStateGraph
sys.modules["langgraph"] = types.ModuleType("langgraph")
sys.modules["langgraph.graph"] = langgraph_graph_stub

langgraph_state_stub = types.ModuleType("langgraph.graph.state")


class _CompiledStateGraph:
    pass


langgraph_state_stub.CompiledStateGraph = _CompiledStateGraph
sys.modules["langgraph.graph.state"] = langgraph_state_stub

logfire_stub = types.ModuleType("logfire")


class _Span:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def set_attributes(self, *a, **k):
        pass


logfire_stub.span = lambda *a, **k: _Span()
logfire_stub.trace = lambda *a, **k: None
sys.modules["logfire"] = logfire_stub


# Additional stubs for orchestrator dependencies
async def _dummy_async(*_args, **_kwargs):
    return None


from core.orchestrator import GraphOrchestrator  # noqa: E402


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
