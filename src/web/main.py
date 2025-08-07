"""Application entrypoint for the FastAPI server."""

# ruff: noqa: E402
from __future__ import annotations

import argparse
import os
from pathlib import Path

from observability import init_observability, instrument_app

init_observability()

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agents.cache_backed_researcher import CacheBackedResearcher
from agents.researcher_web import PerplexityClient, TavilyClient
from config import Settings, load_settings
from core.orchestrator import GraphOrchestrator
from persistence.database import get_db_session, init_db


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""

    settings = load_settings()
    app = FastAPI()
    app.state.settings = settings

    instrument_app(app)

    # Bind search and fact-checking behaviour depending on offline mode.
    if settings.offline_mode:
        app.state.research_client = CacheBackedResearcher()
        app.state.fact_check_offline = True
    else:
        if settings.search_provider == "tavily":
            app.state.research_client = TavilyClient(settings.tavily_api_key or "")
        else:
            app.state.research_client = PerplexityClient(settings.perplexity_api_key)
        app.state.fact_check_offline = False

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def _startup() -> None:
        await setup_database(app)
        setup_graph(app)

    register_routes(app)
    mount_frontend(app)
    return app


async def setup_database(app: FastAPI) -> None:
    """Connect to SQLite, apply migrations and attach session factory."""

    settings: Settings = app.state.settings
    db_path = await init_db(settings)

    async def _session_factory():
        async with get_db_session(db_path) as session:
            yield session

    app.state.db = _session_factory
    app.state.db_path = str(db_path)


def setup_graph(app: FastAPI) -> None:
    """Initialize the application graph."""

    orchestrator = GraphOrchestrator()
    orchestrator.initialize_graph()
    orchestrator.register_edges()
    app.state.graph = orchestrator.graph


def mount_frontend(app: FastAPI) -> None:
    """Serve the built frontend from `frontend/dist`."""

    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    index_file = frontend_dist / "index.html"
    if frontend_dist.exists() and index_file.exists():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    else:

        @app.get("/", include_in_schema=False)
        async def root() -> dict[str, str]:
            """Fallback response when frontend assets are missing."""
            return {"detail": "Frontend build not found"}


def register_routes(app: FastAPI) -> None:
    """Include API routers."""

    from .alert_endpoint import post_alerts
    from .metrics_endpoint import get_metrics
    from .routes import citation, control, entries, export, stream

    app.include_router(stream.router)
    app.include_router(control.router)
    app.include_router(export.router)
    app.include_router(citation.router)
    app.include_router(entries.router)
    app.add_api_route("/metrics", get_metrics, methods=["GET"])
    app.add_api_route("/alerts/{workspace_id}", post_alerts, methods=["POST"])


def main() -> None:
    """CLI entrypoint to launch the Uvicorn server."""

    parser = argparse.ArgumentParser(description="Run the FastAPI server")
    parser.add_argument("--offline", action="store_true", help="Run in offline mode")
    args = parser.parse_args()

    if args.offline:
        os.environ["OFFLINE_MODE"] = "1"

    # Ensure settings reflect any environment overrides before app creation.
    load_settings()

    uvicorn.run(create_app())


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
