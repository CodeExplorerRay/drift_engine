from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from config.settings import Settings
from drift_engine import __version__
from drift_engine.api.dependencies import settings_dependency
from drift_engine.api.schemas.common import HealthResponse
from drift_engine.storage.postgres import check_database

router = APIRouter(prefix="/health", tags=["health"])
SETTINGS_DEP = Depends(settings_dependency)


@router.get("/live", response_model=HealthResponse)
async def live(settings: Settings = SETTINGS_DEP) -> HealthResponse:
    return HealthResponse(status="ok", service=settings.service_name, version=__version__)


@router.get("/ready", response_model=HealthResponse)
async def ready(
    request: Request,
    settings: Settings = SETTINGS_DEP,
) -> HealthResponse | JSONResponse:
    details: dict[str, object] = {
        "environment": settings.environment,
        "storage_backend": settings.resolved_storage_backend,
    }
    database = getattr(request.app.state, "db_engine", None)
    if database is not None:
        try:
            await check_database(database)
            details["database"] = "ok"
        except Exception as error:
            details["database"] = "failed"
            details["database_error"] = error.__class__.__name__
            return JSONResponse(
                status_code=503,
                content=HealthResponse(
                    status="not_ready",
                    service=settings.service_name,
                    version=__version__,
                    details=details,
                ).model_dump(),
            )

    return HealthResponse(
        status="ready",
        service=settings.service_name,
        version=__version__,
        details=details,
    )
