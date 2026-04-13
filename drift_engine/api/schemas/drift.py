from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, Field

from drift_engine.core.models import (
    DriftFinding,
    DriftReport,
    DriftStatus,
    DriftSummary,
    DriftType,
    Severity,
)


class DriftRunRequest(BaseModel):
    baseline_id: str
    collector_names: list[str] | None = None
    auto_remediate: bool = False
    scope: dict[str, Any] = Field(default_factory=dict)


class CollectRequest(BaseModel):
    collector_names: list[str] | None = None
    scope: dict[str, Any] = Field(default_factory=dict)


class DriftFindingResponse(BaseModel):
    id: str
    baseline_id: str
    snapshot_id: str
    resource_key: str
    resource_type: str
    drift_type: str
    path: str
    expected: Any
    actual: Any
    severity: str
    risk_score: float
    status: str
    policy_violations: list[str]
    detected_at: str
    fingerprint: str

    @classmethod
    def from_domain(cls, finding: DriftFinding) -> DriftFindingResponse:
        return cls(**finding.to_document())


class DriftReportResponse(BaseModel):
    id: str
    baseline_id: str
    snapshot_id: str
    generated_at: str
    findings: list[DriftFindingResponse]
    policy_results: list[dict[str, Any]]
    risk_score: float
    summary: dict[str, Any]

    @classmethod
    def from_domain(cls, report: DriftReport) -> DriftReportResponse:
        document = report.to_document()
        document["findings"] = [DriftFindingResponse.from_domain(item) for item in report.findings]
        return cls(**document)


def drift_report_from_document(document: dict[str, Any]) -> DriftReport:
    findings = []
    for item in document.get("findings", []):
        detected_at = item.get("detected_at")
        findings.append(
            DriftFinding(
                id=item["id"],
                baseline_id=item["baseline_id"],
                snapshot_id=item["snapshot_id"],
                resource_key=item["resource_key"],
                resource_type=item["resource_type"],
                drift_type=DriftType(item["drift_type"]),
                path=item["path"],
                expected=item.get("expected"),
                actual=item.get("actual"),
                severity=Severity(item.get("severity", "medium")),
                risk_score=float(item.get("risk_score", 0)),
                status=DriftStatus(item.get("status", "open")),
                policy_violations=item.get("policy_violations", []),
                detected_at=dt.datetime.fromisoformat(detected_at)
                if detected_at
                else dt.datetime.now(dt.UTC),
                fingerprint=item.get("fingerprint", ""),
            )
        )
    summary = document.get("summary", {})
    generated_at = document.get("generated_at")
    return DriftReport(
        id=document["id"],
        baseline_id=document["baseline_id"],
        snapshot_id=document["snapshot_id"],
        findings=findings,
        generated_at=dt.datetime.fromisoformat(generated_at)
        if generated_at
        else dt.datetime.now(dt.UTC),
        policy_results=document.get("policy_results", []),
        risk_score=float(document.get("risk_score", 0)),
        summary=DriftSummary(
            total=int(summary.get("total", len(findings))),
            added=int(summary.get("added", 0)),
            removed=int(summary.get("removed", 0)),
            modified=int(summary.get("modified", 0)),
            by_severity=summary.get("by_severity", {}),
        ),
    )
