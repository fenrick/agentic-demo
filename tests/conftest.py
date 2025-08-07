"""Pytest configuration and lightweight dependency stubs.

Adds the project's ``src`` directory to ``sys.path`` and provides small
stand-ins for optional third-party packages so tests can execute without
network access or heavyweight installations.
"""

from __future__ import annotations

import contextlib
import importlib
import os
import sys
import types
from pathlib import Path

# Compute the absolute path to the project root and ``src`` directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# Prepend ``src`` to ``sys.path`` if it's not already present.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ---------------------------------------------------------------------------
# Lightweight stubs for optional third-party dependencies
# ---------------------------------------------------------------------------

# Provide dummy environment keys expected by the settings module.
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("PERPLEXITY_API_KEY", "test")

# Minimal ``tiktoken`` replacement used by the orchestrator token counter.
tiktoken_stub = types.ModuleType("tiktoken")
setattr(
    tiktoken_stub,
    "encoding_for_model",
    lambda _name: types.SimpleNamespace(encode=lambda s: []),
)  # type: ignore[attr-defined]
setattr(
    tiktoken_stub,
    "get_encoding",
    lambda _name: types.SimpleNamespace(encode=lambda s: []),
)  # type: ignore[attr-defined]
sys.modules.setdefault("tiktoken", tiktoken_stub)

# Basic LangSmith client and tracing helpers used for instrumentation.


class _Client:  # pragma: no cover - simple placeholder
    def __init__(self, *args, **kwargs) -> None:
        pass


langsmith_stub = types.ModuleType("langsmith")
langsmith_stub.Client = _Client  # type: ignore[attr-defined]
sys.modules.setdefault("langsmith", langsmith_stub)

run_helpers_stub = types.ModuleType("langsmith.run_helpers")
run_helpers_stub.trace = lambda *a, **k: contextlib.nullcontext()  # type: ignore[attr-defined]
sys.modules.setdefault("langsmith.run_helpers", run_helpers_stub)

# Minimal loguru stub to satisfy the logging module.


class _Logger:
    def remove(self, *a, **k) -> None:  # pragma: no cover - simple stub
        pass

    def add(self, *a, **k) -> None:  # pragma: no cover - simple stub
        pass

    def bind(self, **_k):  # pragma: no cover - simple stub
        return self

    def info(self, *a, **k) -> None:  # pragma: no cover - simple stub
        pass

    def exception(self, *a, **k) -> None:  # pragma: no cover - simple stub
        pass


loguru_stub = types.ModuleType("loguru")
loguru_stub.logger = _Logger()  # type: ignore[attr-defined]
sys.modules.setdefault("loguru", loguru_stub)

# Provide an ``opentelemetry`` tracer that acts as a no-op context manager.


class _Tracer:
    def start_as_current_span(self, _name):  # pragma: no cover - simple stub
        class _Span:
            def __enter__(self):
                return None

            def __exit__(self, exc_type, exc, tb):
                pass

        return _Span()


opentelemetry_stub = types.ModuleType("opentelemetry")
setattr(
    opentelemetry_stub,
    "trace",
    types.SimpleNamespace(get_tracer=lambda _name: _Tracer()),
)  # type: ignore[attr-defined]
sys.modules.setdefault("opentelemetry", opentelemetry_stub)

# Simplified persistence layer used by the orchestrator when logging actions.


async def get_db_session():  # pragma: no cover - helper for tests
    class _Ctx:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            pass

    return _Ctx()


persistence_stub = types.ModuleType("persistence")
persistence_stub.get_db_session = get_db_session  # type: ignore[attr-defined]
sys.modules.setdefault("persistence", persistence_stub)

persistence_logs_stub = types.ModuleType("persistence.logs")
persistence_logs_stub.compute_hash = lambda _: "hash"  # type: ignore[attr-defined]


async def log_action(*_a, **_k):  # pragma: no cover - helper for tests
    pass


persistence_logs_stub.log_action = log_action  # type: ignore[attr-defined]
sys.modules.setdefault("persistence.logs", persistence_logs_stub)

# Planner stub to satisfy imports without pulling heavy dependencies.


class PlanResult:  # pragma: no cover - simple container
    def __init__(self, confidence: float = 0.0):
        self.confidence = confidence


async def run_planner(state):  # pragma: no cover - placeholder
    return PlanResult(1.0)


agents_planner_stub = types.ModuleType("agents.planner")
agents_planner_stub.PlanResult = PlanResult  # type: ignore[attr-defined]
agents_planner_stub.run_planner = run_planner  # type: ignore[attr-defined]
sys.modules["agents.planner"] = agents_planner_stub
importlib.import_module("agents")
