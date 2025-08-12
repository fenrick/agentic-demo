"""Application entrypoint for the FastAPI server."""

# flake8: noqa
# ruff: noqa: E402

from __future__ import annotations

from observability import init_observability  # isort: skip_file

init_observability()

import argparse
import os
from contextlib import asynccontextmanager
from pathlib import Path

from observability import instrument_app
import httpx
from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

import config
from agents.cache_backed_researcher import CacheBackedResearcher
from agents.researcher_web import TavilyClient
from config import Settings
from core.orchestrator import graph_orchestrator
from persistence.database import get_db_session, init_db
from web.telemetry import REQUEST_COUNTER


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage application startup and shutdown tasks."""

        settings = config.load_settings()
        app.state.settings = settings

        if settings.enable_tracing:
            instrument_app(app)

        # Bind search and fact-checking behaviour depending on offline mode.
        if settings.offline_mode:
            app.state.research_client = CacheBackedResearcher()
            app.state.fact_check_offline = True
        else:
            app.state.research_client = TavilyClient(settings.tavily_api_key or "")
            app.state.fact_check_offline = False

        app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0))

        await setup_database(app)
        setup_graph(app)

        try:
            yield
        finally:
            await app.state.research_client.aclose()
            await app.state.http.aclose()

    app = FastAPI(lifespan=lifespan)

    @app.middleware("http")
    async def _count_requests(request: Request, call_next):
        response = await call_next(request)
        REQUEST_COUNTER.add(1, {"method": request.method, "path": request.url.path})
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
    """Expose the orchestrator instance on the application state."""

    app.state.graph = graph_orchestrator


def mount_frontend(app: FastAPI, settings: Settings | None = None) -> None:
    """Serve built frontend assets and provide history-fallback routing.

    Parameters
    ----------
    app:
        FastAPI application instance to mount the frontend on.
    settings:
        Optional settings instance. When ``None``, the function attempts to
        retrieve settings from ``app.state`` and falls back to global settings.
    """

    settings = settings or getattr(app.state, "settings", config.load_settings())
    dist = Path(settings.frontend_dist)
    if not dist.exists():

        @app.get("/", include_in_schema=False)
        async def root() -> dict[str, str]:
            """Fallback response when frontend assets are missing."""
            return {"detail": "Frontend build not found"}

        return

    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        index = dist / "index.html"
        if index.exists() and not full_path.startswith("api/"):
            return FileResponse(index)
        return JSONResponse({"detail": "Not Found"}, status_code=404)


def register_routes(app: FastAPI) -> None:
    """Include API routers."""

    from .alert_endpoint import post_alerts
    from .auth import verify_jwt
    from .health_endpoint import healthz, readyz
    from .metrics_endpoint import get_metrics
    from .routes import citation, control, entries, export, stream

    # SSE routes are mounted directly to avoid JWT requirements on EventSource.
    app.include_router(stream.router)

    api_router = APIRouter(prefix="/api", dependencies=[Depends(verify_jwt)])
    api_router.include_router(control.router)
    api_router.include_router(export.router)
    api_router.include_router(citation.router)
    api_router.include_router(entries.router)
    api_router.add_api_route("/alerts/{workspace_id}", post_alerts, methods=["POST"])
    app.include_router(api_router)
    app.add_api_route("/metrics", get_metrics, methods=["GET"])
    app.add_api_route("/healthz", healthz, methods=["GET"], include_in_schema=False)
    app.add_api_route("/readyz", readyz, methods=["GET"], include_in_schema=False)


def main() -> None:
    """CLI entrypoint to launch the Uvicorn server."""

    parser = argparse.ArgumentParser(description="Run the FastAPI server")
    parser.add_argument("--offline", action="store_true", help="Run in offline mode")
    args = parser.parse_args()

    if args.offline:
        os.environ["OFFLINE_MODE"] = "1"
        config.load_settings.cache_clear()

    import uvicorn

    uvicorn.run(create_app())


# Make the ASGI app importable by uvicorn and tests
app = create_app()

if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
