from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from drift_engine.utils.serialization import canonical_hash


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DriftType(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


class DriftStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    REMEDIATED = "remediated"
    SUPPRESSED = "suppressed"


class CollectorStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ResourceType(StrEnum):
    FILE = "file"
    PACKAGE = "package"
    SERVICE = "service"
    NETWORK = "network"
    USER = "user"
    KUBERNETES = "kubernetes"
    AWS = "aws"
    AZURE = "azure"
    CUSTOM = "custom"


SEVERITY_BASE_RISK: dict[Severity, float] = {
    Severity.INFO: 1.0,
    Severity.LOW: 10.0,
    Severity.MEDIUM: 30.0,
    Severity.HIGH: 65.0,
    Severity.CRITICAL: 90.0,
}


@dataclass(slots=True)
class ResourceIdentity:
    provider: str
    resource_type: str
    resource_id: str
    account: str | None = None
    region: str | None = None
    tags: dict[str, str] = field(default_factory=dict)

    @property
    def key(self) -> str:
        parts = [
            self.provider.strip().lower(),
            self.account or "_",
            self.region or "_",
            self.resource_type.strip().lower(),
            self.resource_id.strip(),
        ]
        return "::".join(parts)


@dataclass(slots=True)
class StateSnapshot:
    source: str
    resources: dict[str, dict[str, Any]]
    id: str = field(default_factory=lambda: new_id("snap"))
    collected_at: dt.datetime = field(default_factory=utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    checksum: str = ""

    def __post_init__(self) -> None:
        if not self.checksum:
            self.checksum = canonical_hash(
                {"source": self.source, "resources": self.resources, "metadata": self.metadata}
            )

    def to_document(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "resources": self.resources,
            "collected_at": self.collected_at.isoformat(),
            "metadata": self.metadata,
            "checksum": self.checksum,
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> StateSnapshot:
        collected_at = document.get("collected_at")
        if isinstance(collected_at, str):
            collected_at = dt.datetime.fromisoformat(collected_at)
        return cls(
            id=document["id"],
            source=document["source"],
            resources=document.get("resources", {}),
            collected_at=collected_at or utcnow(),
            metadata=document.get("metadata", {}),
            checksum=document.get("checksum", ""),
        )


@dataclass(slots=True)
class Baseline:
    name: str
    resources: dict[str, dict[str, Any]]
    version: str = "1.0.0"
    id: str = field(default_factory=lambda: new_id("base"))
    created_at: dt.datetime = field(default_factory=utcnow)
    scope: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    checksum: str = ""
    signature: str | None = None

    def __post_init__(self) -> None:
        if not self.checksum:
            self.checksum = canonical_hash(self.content_document())

    def content_document(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "resources": self.resources,
            "created_at": self.created_at.isoformat(),
            "scope": self.scope,
            "metadata": self.metadata,
        }

    def unsigned_document(self) -> dict[str, Any]:
        return {**self.content_document(), "checksum": self.checksum}

    def to_document(self) -> dict[str, Any]:
        return {**self.unsigned_document(), "signature": self.signature}

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> Baseline:
        created_at = document.get("created_at")
        if isinstance(created_at, str):
            created_at = dt.datetime.fromisoformat(created_at)
        return cls(
            id=document["id"],
            name=document["name"],
            version=document.get("version", "1.0.0"),
            resources=document.get("resources", {}),
            created_at=created_at or utcnow(),
            scope=document.get("scope", {}),
            metadata=document.get("metadata", {}),
            checksum=document.get("checksum", ""),
            signature=document.get("signature"),
        )


@dataclass(slots=True)
class DriftFinding:
    baseline_id: str
    snapshot_id: str
    resource_key: str
    resource_type: str
    drift_type: DriftType
    path: str
    expected: Any
    actual: Any
    severity: Severity = Severity.MEDIUM
    risk_score: float = 0.0
    id: str = field(default_factory=lambda: new_id("drift"))
    status: DriftStatus = DriftStatus.OPEN
    policy_violations: list[str] = field(default_factory=list)
    detected_at: dt.datetime = field(default_factory=utcnow)
    fingerprint: str = ""

    def __post_init__(self) -> None:
        if not self.risk_score:
            self.risk_score = SEVERITY_BASE_RISK[self.severity]
        if not self.fingerprint:
            self.fingerprint = canonical_hash(
                {
                    "baseline_id": self.baseline_id,
                    "resource_key": self.resource_key,
                    "drift_type": self.drift_type.value,
                    "path": self.path,
                    "expected": self.expected,
                    "actual": self.actual,
                }
            )

    def to_document(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "baseline_id": self.baseline_id,
            "snapshot_id": self.snapshot_id,
            "resource_key": self.resource_key,
            "resource_type": self.resource_type,
            "drift_type": self.drift_type.value,
            "path": self.path,
            "expected": self.expected,
            "actual": self.actual,
            "severity": self.severity.value,
            "risk_score": self.risk_score,
            "status": self.status.value,
            "policy_violations": self.policy_violations,
            "detected_at": self.detected_at.isoformat(),
            "fingerprint": self.fingerprint,
        }


@dataclass(slots=True)
class DriftSummary:
    total: int = 0
    added: int = 0
    removed: int = 0
    modified: int = 0
    by_severity: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class DriftReport:
    baseline_id: str
    snapshot_id: str
    findings: list[DriftFinding]
    id: str = field(default_factory=lambda: new_id("report"))
    generated_at: dt.datetime = field(default_factory=utcnow)
    policy_results: list[dict[str, Any]] = field(default_factory=list)
    risk_score: float = 0.0
    summary: DriftSummary = field(default_factory=DriftSummary)

    def __post_init__(self) -> None:
        if self.summary.total == 0:
            self.summary = self.build_summary(self.findings)
        if not self.risk_score and self.findings:
            self.risk_score = self.aggregate_risk(self.findings)

    @staticmethod
    def build_summary(findings: list[DriftFinding]) -> DriftSummary:
        summary = DriftSummary(total=len(findings))
        for finding in findings:
            if finding.drift_type == DriftType.ADDED:
                summary.added += 1
            elif finding.drift_type == DriftType.REMOVED:
                summary.removed += 1
            elif finding.drift_type == DriftType.MODIFIED:
                summary.modified += 1
            summary.by_severity[finding.severity.value] = (
                summary.by_severity.get(finding.severity.value, 0) + 1
            )
        return summary

    @staticmethod
    def aggregate_risk(findings: list[DriftFinding]) -> float:
        if not findings:
            return 0.0
        risks = sorted((finding.risk_score for finding in findings), reverse=True)
        # Preserve the highest-risk finding while allowing additional findings to add density.
        return round(min(100.0, risks[0] + (sum(risks[1:]) * 0.15)), 2)

    def to_document(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "baseline_id": self.baseline_id,
            "snapshot_id": self.snapshot_id,
            "generated_at": self.generated_at.isoformat(),
            "findings": [finding.to_document() for finding in self.findings],
            "policy_results": self.policy_results,
            "risk_score": self.risk_score,
            "summary": {
                "total": self.summary.total,
                "added": self.summary.added,
                "removed": self.summary.removed,
                "modified": self.summary.modified,
                "by_severity": self.summary.by_severity,
            },
        }


@dataclass(slots=True)
class CollectorResult:
    collector_name: str
    status: CollectorStatus
    snapshot: StateSnapshot | None = None
    duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EngineRunResult:
    report: DriftReport
    snapshot: StateSnapshot
    baseline: Baseline
    collector_results: list[CollectorResult] = field(default_factory=list)
    remediations: list[dict[str, Any]] = field(default_factory=list)
