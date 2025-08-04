import sys
import types
from contextlib import asynccontextmanager
from io import StringIO
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_wrap_traces_with_langsmith_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy_settings = types.SimpleNamespace(model_name="m", data_dir=Path("./workspace"))
    agentic_demo_config = types.SimpleNamespace(MODEL_NAME="m", settings=dummy_settings)
    sys.modules["agentic_demo"] = types.SimpleNamespace(config=agentic_demo_config)
    sys.modules["agentic_demo.config"] = types.SimpleNamespace(
        Settings=lambda: dummy_settings, settings=dummy_settings
    )
    sys.modules["persistence"] = types.SimpleNamespace(get_db_session=None)
    sys.modules["persistence.logs"] = types.SimpleNamespace(
        compute_hash=lambda _: "h", log_action=lambda *a, **k: None
    )
    sys.modules["agents.planner"] = types.SimpleNamespace(PlanResult=object)

    class DummyCheckpoint:
        def __init__(self, *args, **kwargs) -> None:  # noqa: ANN001
            pass

        async def save_checkpoint(self, state) -> None:  # noqa: ANN001
            pass

    sys.modules["core.checkpoint"] = types.SimpleNamespace(
        SqliteCheckpointManager=DummyCheckpoint
    )

    class DummyStateModule:
        class State:  # noqa: D401
            """Minimal State stub."""

            def __init__(self, prompt: str = "p") -> None:
                self.prompt = prompt

            def to_dict(self) -> dict:
                return {"prompt": self.prompt}

    sys.modules["core.state"] = DummyStateModule

    class DummyEncoding:
        def encode(self, text: str) -> bytes:  # noqa: ANN001
            return text.encode()

    class DummyTiktoken:
        def encoding_for_model(self, model: str):  # noqa: ANN001
            raise KeyError

        def get_encoding(self, name: str) -> DummyEncoding:  # noqa: ANN001
            return DummyEncoding()

    sys.modules["tiktoken"] = DummyTiktoken()

    class DummyCompiled:
        def get_graph(self):  # noqa: ANN001
            return types.SimpleNamespace(nodes={}, edges=[])

    class DummyStateGraph:
        def __init__(self, state_cls) -> None:  # noqa: ANN001
            self.nodes = {}
            self.edges = []

        def add_node(self, *args, **kwargs) -> None:  # noqa: ANN001, ANN002
            pass

        def add_edge(self, *args, **kwargs) -> None:  # noqa: ANN001, ANN002
            pass

        def add_conditional_edges(self, *a, **k) -> None:  # noqa: ANN001, ANN002
            pass

        def compile(self) -> DummyCompiled:
            return DummyCompiled()

    sys.modules["langgraph.graph"] = types.SimpleNamespace(
        END="__end__",
        START="__start__",
        StateGraph=DummyStateGraph,
    )
    sys.modules["langgraph.graph.state"] = types.SimpleNamespace(
        CompiledStateGraph=DummyCompiled
    )

    real_open = Path.open

    def fake_open(self, *args, **kwargs):  # noqa: ANN001
        if self.name.endswith("langgraph.json"):
            return StringIO('{"nodes": [], "edges": []}')
        return real_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fake_open)

    from core.orchestrator import GraphOrchestrator

    calls: list[str] = []

    class DummyRun:
        def __init__(self, name: str) -> None:
            self.name = name
            self.outputs: object | None = None

        def end(self, *, outputs: object) -> None:  # noqa: ANN001
            self.outputs = outputs

    class DummyClient:
        def trace(self, name: str, *, inputs: object | None = None):  # noqa: ANN001
            calls.append(name)

            class Ctx:
                def __enter__(self) -> DummyRun:  # type: ignore[override]
                    return DummyRun(name)

                def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
                    return None

            return Ctx()

    async def fake_log_action(*args, **kwargs) -> None:  # noqa: ANN001, ANN002
        return None

    @asynccontextmanager
    async def fake_session():
        yield None

    monkeypatch.setattr("core.orchestrator.log_action", fake_log_action)
    monkeypatch.setattr("core.orchestrator.get_db_session", fake_session)

    client = DummyClient()
    orch = GraphOrchestrator(langsmith_client=client)

    async def node(state: DummyStateModule.State) -> str:  # noqa: ANN001
        return "ok"

    state = DummyStateModule.State()
    await orch._wrap("Trace", node)(state)
    assert calls == ["Trace"]
