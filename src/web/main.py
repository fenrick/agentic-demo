"""Application entrypoint for the FastAPI server."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import load_settings, Settings
from core.checkpoint import SqliteCheckpointManager
from core.orchestrator import GraphOrchestrator
from persistence.database import init_db, get_db_session

from agents.cache_backed_researcher import CacheBackedResearcher
from agents.researcher_web import PerplexityClient


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""

    settings = load_settings()
    app = FastAPI()
    app.state.settings = settings

    # Bind search and fact-checking behaviour depending on offline mode.
    if settings.offline_mode:
        app.state.research_client = CacheBackedResearcher()
        app.state.fact_check_offline = True
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


def setup_graph(app: FastAPI) -> None:
    """Initialize the LangGraph ``StateGraph`` and checkpoint saver."""

    settings: Settings = app.state.settings
    checkpoint_path = settings.data_dir / "checkpoint.db"
    manager = SqliteCheckpointManager(str(checkpoint_path))
    orchestrator = GraphOrchestrator(manager)
    orchestrator.initialize_graph()
    orchestrator.register_edges()
    app.state.graph = orchestrator.graph


def mount_frontend(app: FastAPI) -> None:
    """Serve the React build directory at the root path."""

    dist_path = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if dist_path.exists():
        app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")


def register_routes(app: FastAPI) -> None:
    """Include API routers."""

    from .routes import stream, control, export, citation

    app.include_router(stream.router)
    app.include_router(control.router)
    app.include_router(export.router)
    app.include_router(citation.router)


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
