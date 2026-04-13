from __future__ import annotations

from fastapi import APIRouter, Depends

from config.settings import Settings
from drift_engine.api.dependencies import settings_dependency
from drift_engine.api.schemas.integration import IntegrationCheckResponse, IntegrationResponse
from drift_engine.integrations.kubernetes import KubernetesIntegrationChecker
from drift_engine.integrations.registry import build_integration_catalog

router = APIRouter(prefix="/integrations", tags=["integrations"])
SETTINGS_DEP = Depends(settings_dependency)


@router.get("", response_model=list[IntegrationResponse])
async def list_integrations(settings: Settings = SETTINGS_DEP) -> list[IntegrationResponse]:
    return [
        IntegrationResponse.from_domain(integration)
        for integration in build_integration_catalog(settings)
    ]


@router.get("/kubernetes/check", response_model=IntegrationCheckResponse)
async def check_kubernetes(
    namespaces: str | None = None,
    settings: Settings = SETTINGS_DEP,
) -> IntegrationCheckResponse:
    namespace_values = (
        Settings._csv_values(namespaces) if namespaces else settings.kubernetes_namespace_values
    )
    checker = KubernetesIntegrationChecker(timeout_seconds=settings.collector_timeout_seconds)
    return IntegrationCheckResponse(**await checker.check(namespace_values))
