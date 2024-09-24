"""FastAPI application factory."""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.db.session import create_engine, create_session_factory, init_db

log = get_logger("main")

OPENAPI_TAGS = [
    {"name": "health", "description": "Liveness and dependency checks."},
    {"name": "auth", "description": "Registration, login, token refresh and profile."},
    {"name": "notebooks", "description": "Group notes into notebooks."},
    {"name": "notes", "description": "Notes with version history and soft delete."},
    {"name": "tags", "description": "Tags derived from notes."},
    {"name": "search", "description": "Keyword, semantic and hybrid search."},
    {"name": "ai", "description": "Summaries, tag suggestions and chat with your notes."},
]


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings.database_url)
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        if settings.environment != "production" or settings.is_sqlite:
            # Production Postgres deployments run Alembic; dev/test create tables directly.
            await init_db(engine)
        log.info(
            "%s v%s started (env=%s, db=%s, ai=%s)",
            settings.app_name,
            __version__,
            settings.environment,
            "sqlite" if settings.is_sqlite else "postgresql",
            settings.ai_provider,
        )
        try:
            yield
        finally:
            await engine.dispose()
            log.info("engine disposed")

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="AI-powered knowledge notes: summaries, auto-tags, semantic search and chat.",
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"
        return response

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"name": settings.app_name, "version": __version__, "docs": "/docs"}

    return app


app = create_app()
