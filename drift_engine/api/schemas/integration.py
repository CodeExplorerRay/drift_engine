from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from drift_engine.integrations.models import IntegrationDescriptor


class IntegrationResponse(BaseModel):
    name: str
    display_name: str
    collector_name: str
    description: str
    enabled: bool
    status: str
    resource_types: list[str]
    optional_dependencies: list[str]
    required_configuration: list[str]
    missing: list[str]
    settings: dict[str, Any]
    setup_hint: str

    @classmethod
    def from_domain(cls, integration: IntegrationDescriptor) -> IntegrationResponse:
        return cls(**integration.to_document())


class IntegrationCheckItem(BaseModel):
    name: str
    status: str
    details: dict[str, Any]
    error: str | None = None


class IntegrationCheckResponse(BaseModel):
    integration: str
    ready: bool
    context: str | None = None
    namespaces: list[str]
    checks: list[IntegrationCheckItem]
