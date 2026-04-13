from __future__ import annotations

from fastapi import APIRouter, Depends

from config.settings import Settings
from drift_engine.api.dependencies import request_engine as get_engine
from drift_engine.api.dependencies import settings_dependency
from drift_engine.core.engine import DriftEngine
from drift_engine.integrations.registry import build_integration_catalog

router = APIRouter(prefix="/collectors", tags=["collectors"])
ENGINE_DEP = Depends(get_engine)
SETTINGS_DEP = Depends(settings_dependency)


@router.get("")
async def list_collectors(
    engine: DriftEngine = ENGINE_DEP,
    settings: Settings = SETTINGS_DEP,
) -> list[dict[str, object]]:
    integrations = {
        integration.collector_name: integration
        for integration in build_integration_catalog(settings)
    }
    response: list[dict[str, object]] = []
    for name in engine.collectors.names():
        collector = engine.collectors.get(name)
        integration = integrations.get(name)
        response.append(
            {
                "name": name,
                "enabled": collector.config.enabled,
                "resource_type": collector.resource_type,
                "integration": integration.name if integration is not None else "local",
                "status": integration.status if integration is not None else "ready",
                "description": (
                    integration.description if integration is not None else "Local source"
                ),
            }
        )
    return response
