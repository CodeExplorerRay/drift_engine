from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from config.logging_config import get_logger
from drift_engine.api.middleware.correlation import current_correlation_id
from drift_engine.core.exceptions import DriftEngineError

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DriftEngineError)
    async def drift_error_handler(request: Request, exc: DriftEngineError) -> JSONResponse:
        del request
        logger.warning("domain_error", error=str(exc), correlation_id=current_correlation_id())
        return JSONResponse(
            {
                "error": exc.__class__.__name__,
                "detail": str(exc),
                "correlation_id": current_correlation_id(),
            },
            status_code=400,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        del request
        return JSONResponse(
            {
                "error": "validation_error",
                "detail": str(exc),
                "correlation_id": current_correlation_id(),
            },
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        del request
        logger.exception(
            "unhandled_api_error", error=str(exc), correlation_id=current_correlation_id()
        )
        return JSONResponse(
            {
                "error": "internal_server_error",
                "detail": "an unexpected error occurred",
                "correlation_id": current_correlation_id(),
            },
            status_code=500,
        )
