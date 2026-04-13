from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from drift_engine.core.models import Baseline


class BaselineCreate(BaseModel):
    name: str = Field(min_length=1)
    version: str = "1.0.0"
    resources: dict[str, dict[str, Any]]
    scope: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaselineFromCurrentRequest(BaseModel):
    name: str = Field(min_length=1)
    version: str = "1.0.0"
    collector_names: list[str] | None = None
    scope: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


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
