from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str
    detail: str
    correlation_id: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    details: dict[str, Any] = Field(default_factory=dict)


class PageResponse(BaseModel):
    items: list[dict[str, Any]]
    limit: int
    offset: int
    count: int
