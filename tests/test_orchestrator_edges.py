# mypy: ignore-errors
import contextlib
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
    model_name = "gpt"
    data_dir = Path(".")


config_stub.MODEL_NAME = "gpt"
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

langsmith_stub = types.ModuleType("langsmith")


class _Client:
    def trace(self, *_, **__):
        class _Ctx:
            def __enter__(self):
                return None

            def __exit__(self, *exc):
                pass

            def log_metrics(self, *a, **k):
                pass

            def end(self, *a, **k):
                pass

        return _Ctx()


langsmith_stub.Client = _Client
sys.modules["langsmith"] = langsmith_stub

langsmith_run_stub = types.ModuleType("langsmith.run_helpers")
langsmith_run_stub.trace = lambda *a, **k: contextlib.nullcontext()
sys.modules["langsmith.run_helpers"] = langsmith_run_stub

opentelemetry_stub = types.ModuleType("opentelemetry")


class _Tracer:
    def start_as_current_span(self, _name):
        class _Span:
            def __enter__(self):
                return None

            def __exit__(self, *exc):
                pass

        return _Span()


opentelemetry_stub.trace = types.SimpleNamespace(get_tracer=lambda _name: _Tracer())
sys.modules["opentelemetry"] = opentelemetry_stub


# Additional stubs for orchestrator dependencies
async def _dummy_async(*_args, **_kwargs):
    return None


agents_planner_stub = types.ModuleType("agents.planner")


class PlanResult:  # type: ignore[too-many-ancestors]
    pass


agents_planner_stub.PlanResult = PlanResult
agents_planner_stub.run_planner = _dummy_async
sys.modules.setdefault("agents", types.ModuleType("agents"))
sys.modules["agents.planner"] = agents_planner_stub


# Additional agent stubs referenced by langgraph.json
for _mod, _name in [
    ("agents.researcher_web_node", "run_researcher_web"),
    ("agents.content_weaver", "run_content_weaver"),
    ("agents.pedagogy_critic", "run_pedagogy_critic"),
    ("agents.fact_checker", "run_fact_checker"),
    ("agents.approver", "run_approver"),
    ("agents.exporter", "run_exporter"),
]:
    mod = types.ModuleType(_mod)
    setattr(mod, _name, _dummy_async)
    sys.modules[_mod] = mod

core_policies_stub = types.ModuleType("core.policies")


def policy_retry_on_low_confidence(*_a, **_k):  # type: ignore[no-untyped-def]
    return "continue"


def policy_retry_on_critic_failure(*_a, **_k):  # type: ignore[no-untyped-def]
    return False


core_policies_stub.policy_retry_on_low_confidence = policy_retry_on_low_confidence
core_policies_stub.policy_retry_on_critic_failure = policy_retry_on_critic_failure
sys.modules["core.policies"] = core_policies_stub

core_logging_stub = types.ModuleType("core.logging")


def get_logger(*_args, **_kwargs):  # type: ignore[no-untyped-def]
    class _Logger:
        def info(self, *a, **k):  # type: ignore[no-untyped-def]
            pass

        def exception(self, *a, **k):  # type: ignore[no-untyped-def]
            pass

    return _Logger()


core_logging_stub.get_logger = get_logger
sys.modules["core.logging"] = core_logging_stub

core_state_stub = types.ModuleType("core.state")


class State:  # type: ignore[too-many-ancestors]
    def __init__(self, prompt: str = "") -> None:
        self.prompt = prompt
        self.retries = {}

    def to_dict(self):  # type: ignore[no-untyped-def]
        return {}


core_state_stub.State = State
core_state_stub.Citation = object
sys.modules["core.state"] = core_state_stub

persistence_stub = types.ModuleType("persistence")


async def get_db_session():  # type: ignore[no-untyped-def]
    class _Ctx:
        async def __aenter__(self):  # type: ignore[no-untyped-def]
            return self

        async def __aexit__(self, *exc):  # type: ignore[no-untyped-def]
            pass

    return _Ctx()


persistence_stub.get_db_session = get_db_session
sys.modules["persistence"] = persistence_stub

persistence_logs_stub = types.ModuleType("persistence.logs")


def compute_hash(_):  # type: ignore[no-untyped-def]
    return "hash"


async def log_action(*_a, **_k):  # type: ignore[no-untyped-def]
    pass


persistence_logs_stub.compute_hash = compute_hash
persistence_logs_stub.log_action = log_action
sys.modules["persistence.logs"] = persistence_logs_stub

from core.orchestrator import GraphOrchestrator  # noqa: E402


def dummy_cond(prev, state):  # type: ignore[no-untyped-def]
    return True


def cond_str(prev, state):  # type: ignore[no-untyped-def]
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
