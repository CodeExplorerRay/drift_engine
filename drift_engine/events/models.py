from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from drift_engine.core.models import new_id, utcnow


class EventType(StrEnum):
    BASELINE_CREATED = "baseline.created"
    SNAPSHOT_COLLECTED = "snapshot.collected"
    DRIFT_DETECTED = "drift.detected"
    NO_DRIFT = "drift.none"
    POLICY_VIOLATED = "policy.violated"
    REMEDIATION_PLANNED = "remediation.planned"
    REMEDIATION_EXECUTED = "remediation.executed"


@dataclass(slots=True)
class Event:
    type: EventType
    subject: str
    payload: dict[str, Any]
    id: str = field(default_factory=lambda: new_id("evt"))
    occurred_at: dt.datetime = field(default_factory=utcnow)
    correlation_id: str | None = None

    def to_document(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "subject": self.subject,
            "payload": self.payload,
            "occurred_at": self.occurred_at.isoformat(),
            "correlation_id": self.correlation_id,
        }
