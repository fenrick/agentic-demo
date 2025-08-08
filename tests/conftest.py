"""Pytest configuration and lightweight dependency stubs.

Adds the project's ``src`` directory to ``sys.path`` and provides small
stand-ins for selected third-party packages so tests can execute without
network access or heavyweight installations.
"""

from __future__ import annotations

import importlib
import os
import sys
import types
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, List

import agents  # type: ignore  # noqa: E402,F401

# Compute the absolute path to the project root and ``src`` directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# Prepend ``src`` to ``sys.path`` if it's not already present.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ---------------------------------------------------------------------------
# Lightweight stubs for third-party dependencies
# ---------------------------------------------------------------------------

# Provide dummy environment keys expected by the settings module.
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("PERPLEXITY_API_KEY", "test")

# Minimal ``tiktoken`` replacement used by the orchestrator token counter.
tiktoken_stub = types.ModuleType("tiktoken")
tiktoken_stub.encoding_for_model = (  # type: ignore[attr-defined]
    lambda _name: types.SimpleNamespace(encode=lambda s: [])
)
tiktoken_stub.get_encoding = (  # type: ignore[attr-defined]
    lambda _name: types.SimpleNamespace(encode=lambda s: [])
)
sys.modules.setdefault("tiktoken", tiktoken_stub)


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
opentelemetry_stub.trace = types.SimpleNamespace(  # type: ignore[attr-defined]
    get_tracer=lambda _name: _Tracer()
)
sys.modules.setdefault("opentelemetry", opentelemetry_stub)

# Minimal critic stubs to avoid heavy imports in policy tests.


@dataclass
class DummyCritiqueReport:  # pragma: no cover - simple container
    recommendations: List[str] = field(default_factory=list)


@dataclass
class DummyFactCheckReport:  # pragma: no cover - simple container
    hallucination_count: int = 0
    unsupported_claims_count: int = 0


async def run_fact_checker(*_a, **_k):  # pragma: no cover - helper for tests
    return DummyFactCheckReport()


critics_stub = types.ModuleType("agents.critics")
critics_stub.CritiqueReport = DummyCritiqueReport  # type: ignore[attr-defined]
critics_stub.FactCheckReport = DummyFactCheckReport  # type: ignore[attr-defined]
critics_stub.run_fact_checker = run_fact_checker  # type: ignore[attr-defined]
agents.critics = critics_stub  # type: ignore[attr-defined]
sys.modules["agents.critics"] = critics_stub

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
# Lightweight models and repositories used by research components.


@dataclass
class Citation:  # pragma: no cover - simple container
    url: str
    title: str
    retrieved_at: datetime = datetime.utcnow()
    licence: str = ""


class CitationRepo:  # pragma: no cover - minimal stub
    def __init__(self, *_a, **_k):
        pass

    async def insert(self, *_a, **_k):
        pass


class RetrievalCacheRepo:  # pragma: no cover - minimal cache
    def __init__(self, *_a, **_k):
        pass

    async def get(self, _query: str):
        return None

    async def set(self, _query: str, _results: List[Any]):
        pass


persistence_stub.Citation = Citation  # type: ignore[attr-defined]
persistence_stub.CitationRepo = CitationRepo  # type: ignore[attr-defined]
persistence_stub.RetrievalCacheRepo = RetrievalCacheRepo  # type: ignore[attr-defined]
sys.modules.setdefault("persistence", persistence_stub)

persistence_repos_stub = types.ModuleType("persistence.repositories")
retrieval_cache_repo_stub = types.ModuleType(
    "persistence.repositories.retrieval_cache_repo"
)
retrieval_cache_repo_stub.RetrievalCacheRepo = RetrievalCacheRepo  # type: ignore[attr-defined]
persistence_repos_stub.retrieval_cache_repo = retrieval_cache_repo_stub  # type: ignore[attr-defined]
sys.modules.setdefault("persistence.repositories", persistence_repos_stub)
sys.modules.setdefault(
    "persistence.repositories.retrieval_cache_repo", retrieval_cache_repo_stub
)

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
