from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from drift_engine.api.schemas.drift import validate_collector_names, validate_scope
from drift_engine.core.models import Baseline

MAX_BASELINE_RESOURCES = 5_000
MAX_BASELINE_RESOURCE_KEY_LENGTH = 512


def validate_baseline_resources(
    resources: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    if len(resources) > MAX_BASELINE_RESOURCES:
        raise ValueError(f"baseline resources exceed {MAX_BASELINE_RESOURCES} items")
    for key, value in resources.items():
        if len(key) > MAX_BASELINE_RESOURCE_KEY_LENGTH:
            raise ValueError("baseline resource key is too long")
        if not isinstance(value, dict):
            raise ValueError("baseline resources must map to objects")
    return resources


class BaselineCreate(BaseModel):
    name: str = Field(min_length=1)
    version: str = "1.0.0"
    resources: dict[str, dict[str, Any]]
    scope: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("resources")
    @classmethod
    def validate_resources(cls, value: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return validate_baseline_resources(value)

    @field_validator("scope")
    @classmethod
    def validate_request_scope(cls, value: dict[str, Any]) -> dict[str, Any]:
        return validate_scope(value)


class BaselineFromCurrentRequest(BaseModel):
    name: str = Field(min_length=1)
    version: str = "1.0.0"
    collector_names: list[str] | None = None
    scope: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("collector_names")
    @classmethod
    def validate_collectors(cls, value: list[str] | None) -> list[str] | None:
        return validate_collector_names(value)

    @field_validator("scope")
    @classmethod
    def validate_request_scope(cls, value: dict[str, Any]) -> dict[str, Any]:
        return validate_scope(value)


class BaselineResponse(BaseModel):
    id: str
    name: str
    version: str
    resources: dict[str, dict[str, Any]]
    scope: dict[str, Any]
    metadata: dict[str, Any]
    checksum: str
    signature: str | None
    created_at: str

    @classmethod
    def from_domain(cls, baseline: Baseline) -> BaselineResponse:
        document = baseline.to_document()
        document["created_at"] = baseline.created_at.isoformat()
        return cls(**document)
