from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException, Request, status

from drift_engine.api.middleware.correlation import current_correlation_id
from drift_engine.core.engine import DriftEngine
from drift_engine.core.operations import AuditEvent


class Scopes:
    BASELINE_WRITE = "baseline:write"
    SCAN_EXECUTE = "scan:execute"
    POLICY_WRITE = "policy:write"
    REMEDIATION_PLAN = "remediation:plan"
    REMEDIATION_APPROVE = "remediation:approve"
    REMEDIATION_EXECUTE = "remediation:execute"
    JOB_WRITE = "jobs:write"
    AUDIT_READ = "audit:read"
    ADMIN = "*"


@dataclass(frozen=True, slots=True)
class AuthPrincipal:
    id: str
    scopes: list[str] = field(default_factory=list)
    actor_type: str = "service_account"

    def has_scope(self, scope: str) -> bool:
        return Scopes.ADMIN in self.scopes or scope in self.scopes

    @classmethod
    def local_dev(cls) -> AuthPrincipal:
        return cls(id="local-dev", scopes=[Scopes.ADMIN], actor_type="local")


def request_principal(request: Request) -> AuthPrincipal:
    principal = getattr(request.state, "principal", None)
    if isinstance(principal, AuthPrincipal):
        return principal
    return AuthPrincipal(id="anonymous", scopes=[], actor_type="anonymous")


def require_scope(scope: str) -> Callable[[Request], AuthPrincipal]:
    def dependency(request: Request) -> AuthPrincipal:
        principal = request_principal(request)
        if not principal.has_scope(scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"scope {scope!r} required",
            )
        return principal

    return dependency


async def audit_action(
    *,
    engine: DriftEngine,
    request: Request,
    action: str,
    target_type: str,
    target_id: str,
    details: dict[str, Any] | None = None,
) -> None:
    if engine.audit_repository is None:
        return
    principal = request_principal(request)
    await engine.audit_repository.save(
        AuditEvent(
            action=action,
            actor_id=principal.id,
            actor_type=principal.actor_type,
            scopes=principal.scopes,
            target_type=target_type,
            target_id=target_id,
            details=details or {},
            correlation_id=current_correlation_id(),
        )
    )
