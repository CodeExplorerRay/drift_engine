from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from drift_engine.core.models import new_id, utcnow


class JobRunStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(slots=True)
class AuditEvent:
    action: str
    actor_id: str
    target_type: str
    target_id: str
    details: dict[str, Any] = field(default_factory=dict)
    actor_type: str = "service_account"
    scopes: list[str] = field(default_factory=list)
    correlation_id: str | None = None
    id: str = field(default_factory=lambda: new_id("audit"))
    created_at: dt.datetime = field(default_factory=utcnow)

    def to_document(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "scopes": self.scopes,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "details": self.details,
            "correlation_id": self.correlation_id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> AuditEvent:
        created_at = document.get("created_at")
        return cls(
            id=document["id"],
            action=document["action"],
            actor_id=document["actor_id"],
            actor_type=document.get("actor_type", "service_account"),
            scopes=list(document.get("scopes", [])),
            target_type=document["target_type"],
            target_id=document["target_id"],
            details=document.get("details", {}),
            correlation_id=document.get("correlation_id"),
            created_at=dt.datetime.fromisoformat(created_at)
            if created_at
            else dt.datetime.now(dt.UTC),
        )


@dataclass(slots=True)
class ScheduledScanJob:
    name: str
    baseline_id: str
    interval_seconds: int
    collector_names: list[str] | None = None
    enabled: bool = True
    id: str = field(default_factory=lambda: new_id("job"))
    created_at: dt.datetime = field(default_factory=utcnow)
    updated_at: dt.datetime = field(default_factory=utcnow)
    next_run_at: dt.datetime = field(default_factory=utcnow)
    last_run_at: dt.datetime | None = None

    def to_document(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "baseline_id": self.baseline_id,
            "collector_names": self.collector_names,
            "interval_seconds": self.interval_seconds,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "next_run_at": self.next_run_at.isoformat(),
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ScheduledScanJob:
        last_run_at = document.get("last_run_at")
        return cls(
            id=document["id"],
            name=document["name"],
            baseline_id=document["baseline_id"],
            collector_names=document.get("collector_names"),
            interval_seconds=int(document["interval_seconds"]),
            enabled=bool(document.get("enabled", True)),
            created_at=dt.datetime.fromisoformat(document["created_at"]),
            updated_at=dt.datetime.fromisoformat(document["updated_at"]),
            next_run_at=dt.datetime.fromisoformat(document["next_run_at"]),
            last_run_at=dt.datetime.fromisoformat(last_run_at) if last_run_at else None,
        )


@dataclass(slots=True)
class JobRun:
    job_id: str
    status: JobRunStatus = JobRunStatus.RUNNING
    report_id: str | None = None
    error: str = ""
    id: str = field(default_factory=lambda: new_id("jobrun"))
    started_at: dt.datetime = field(default_factory=utcnow)
    finished_at: dt.datetime | None = None

    def to_document(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "status": self.status.value,
            "report_id": self.report_id,
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> JobRun:
        finished_at = document.get("finished_at")
        return cls(
            id=document["id"],
            job_id=document["job_id"],
            status=JobRunStatus(document.get("status", "running")),
            report_id=document.get("report_id"),
            error=document.get("error", ""),
            started_at=dt.datetime.fromisoformat(document["started_at"]),
            finished_at=dt.datetime.fromisoformat(finished_at) if finished_at else None,
        )
