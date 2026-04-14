from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from config.settings import Settings
from drift_engine.api.security import AuthPrincipal
from drift_engine.utils.crypto import secure_compare


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.settings = settings

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in {"/", "/favicon.ico"} or request.url.path.startswith(
            ("/assets", "/health", "/metrics")
        ):
            return await call_next(request)

        configured_accounts = self.settings.service_account_values
        auth_is_active = bool(configured_accounts) or self.settings.is_production
        if not self.settings.auth_required or not auth_is_active:
            request.state.principal = AuthPrincipal.local_dev()
            return await call_next(request)

        provided = request.headers.get("X-API-Key") or ""
        for account in configured_accounts:
            if secure_compare(provided, str(account["key"])):
                request.state.principal = AuthPrincipal(
                    id=str(account["id"]),
                    actor_type=str(account["actor_type"]),
                    scopes=list(account["scopes"]),
                )
                return await call_next(request)
        return JSONResponse(
            {"error": "unauthorized", "detail": "valid X-API-Key required"}, status_code=401
        )
