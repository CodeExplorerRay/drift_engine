from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, Response

from config.logging_config import configure_logging
from config.settings import get_settings
from drift_engine import __version__
from drift_engine.api.dependencies import build_runtime_engine
from drift_engine.api.middleware.auth import ApiKeyAuthMiddleware
from drift_engine.api.middleware.correlation import CorrelationIdMiddleware
from drift_engine.api.middleware.error_handler import register_exception_handlers
from drift_engine.api.middleware.rate_limit import InMemoryRateLimitMiddleware
from drift_engine.api.routes import (
    audit,
    baselines,
    collectors,
    drifts,
    health,
    integrations,
    jobs,
    policies,
    remediation,
    ui,
)
from drift_engine.core.scheduler import DriftJobScheduler
from drift_engine.telemetry.tracing import configure_tracing


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine, database = await build_runtime_engine(settings)
    scheduler: DriftJobScheduler | None = None
    if settings.scheduler_enabled and engine.job_repository is not None:
        scheduler = DriftJobScheduler(
            engine=engine,
            tick_seconds=settings.scheduler_interval_seconds,
            owner_id=settings.scheduler_owner_id,
            lock_ttl_seconds=settings.scheduler_lock_ttl_seconds,
        )
        await scheduler.start()
    app.state.drift_engine = engine
    app.state.db_engine = database
    app.state.storage_backend = settings.resolved_storage_backend
    app.state.scheduler = scheduler
    try:
        yield
    finally:
        if scheduler is not None:
            await scheduler.stop()
        if database is not None:
            await database.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    settings.validate_runtime_security()
    configure_logging(settings.log_level)
    configure_tracing(settings.service_name)

    app = FastAPI(
        title="System Drift Engine",
        version=__version__,
        description=(
            "Continuous infrastructure drift detection, policy enforcement, " "and remediation."
        ),
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        InMemoryRateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute
    )
    app.add_middleware(ApiKeyAuthMiddleware, settings=settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(ui.router)
    app.include_router(health.router)
    app.include_router(baselines.router)
    app.include_router(drifts.router)
    app.include_router(policies.router)
    app.include_router(collectors.router)
    app.include_router(integrations.router)
    app.include_router(remediation.router)
    app.include_router(jobs.router)
    app.include_router(audit.router)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        try:
            from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
        except ImportError:
            return Response("metrics disabled", media_type="text/plain")
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/docs", include_in_schema=False)
    async def swagger_docs() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{app.title} - API docs",
            swagger_favicon_url="/favicon.ico",
        )

    @app.get("/redoc", include_in_schema=False)
    async def redoc_docs() -> HTMLResponse:
        return get_redoc_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{app.title} - ReDoc",
            redoc_favicon_url="/favicon.ico",
        )

    return app


app = create_app()
