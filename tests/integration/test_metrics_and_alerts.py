"""Integration tests for metrics and alert endpoints."""

import sys
import types

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    """Provide a configured :class:`TestClient` instance."""
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "y")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("OFFLINE_MODE", "1")
    fake_settings = types.SimpleNamespace(model_name="gpt-4", perplexity_api_key="x")
    fake_config = types.SimpleNamespace(settings=fake_settings)
    sys.modules["agentic_demo"] = types.ModuleType("agentic_demo")
    sys.modules["agentic_demo.config"] = fake_config
    sys.modules["agentic_demo"].config = fake_config

    class DummyCacheBackedResearcher:  # pragma: no cover - placeholder
        pass

    class DummyPerplexityClient:  # pragma: no cover - placeholder
        def __init__(self, *args, **kwargs) -> None:
            pass

    class DummyTavilyClient:  # pragma: no cover - placeholder
        def __init__(self, *args, **kwargs) -> None:
            pass

    class DummyCheckpointManager:  # pragma: no cover - placeholder
        def __init__(self, *args, **kwargs) -> None:
            pass

    class DummyGraphOrchestrator:  # pragma: no cover - placeholder
        def __init__(self, *args, **kwargs) -> None:
            self.graph = {}

        def initialize_graph(self) -> None:
            pass

        def register_edges(self) -> None:
            pass

    sys.modules["agents.cache_backed_researcher"] = types.SimpleNamespace(
        CacheBackedResearcher=DummyCacheBackedResearcher
    )
    sys.modules["agents.researcher_web"] = types.SimpleNamespace(
        PerplexityClient=DummyPerplexityClient, TavilyClient=DummyTavilyClient
    )
    sys.modules["core.checkpoint"] = types.SimpleNamespace(
        SqliteCheckpointManager=DummyCheckpointManager
    )
    sys.modules["core.orchestrator"] = types.SimpleNamespace(
        GraphOrchestrator=DummyGraphOrchestrator
    )

    from fastapi import APIRouter

    dummy_routes_pkg = types.ModuleType("web.routes")
    sys.modules["web.routes"] = dummy_routes_pkg
    empty_router = APIRouter()
    for name in ["citation", "control", "export", "stream"]:
        module = types.ModuleType(f"web.routes.{name}")
        module.router = empty_router
        setattr(dummy_routes_pkg, name, module)
        sys.modules[f"web.routes.{name}"] = module
    from web.main import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client


def test_metrics_endpoint_returns_success(client: TestClient) -> None:
    """``/metrics`` responds with HTTP 200."""
    res = client.get("/metrics")
    assert res.status_code == 200


def test_alert_endpoint_returns_success(client: TestClient) -> None:
    """``/alerts/{workspace_id}`` responds with HTTP 204."""
    res = client.post("/alerts/ws1")
    assert res.status_code == 204
