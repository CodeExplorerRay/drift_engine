from __future__ import annotations

from dataclasses import dataclass, field

from drift_engine.core.models import DriftFinding, DriftReport, DriftType, new_id
from drift_engine.remediation.actions import RemediationAction


@dataclass(slots=True)
class RemediationPlan:
    report_id: str
    actions: list[RemediationAction]
    id: str = field(default_factory=lambda: new_id("plan"))

    def to_document(self) -> dict[str, object]:
        return {
            "id": self.id,
            "report_id": self.report_id,
            "actions": [action.to_document() for action in self.actions],
        }


class RemediationStrategyRegistry:
    def plan(self, report: DriftReport) -> RemediationPlan:
        return RemediationPlan(
            report_id=report.id,
            actions=[
                action for finding in report.findings for action in self._for_finding(finding)
            ],
        )

    def _for_finding(self, finding: DriftFinding) -> list[RemediationAction]:
        if finding.resource_type == "service" and finding.drift_type == DriftType.MODIFIED:
            service_name = str(finding.resource_key).split("::")[-1]
            return [
                RemediationAction(
                    finding_id=finding.id,
                    fingerprint=finding.fingerprint,
                    strategy="restart_service",
                    description=f"Restart service {service_name} to restore expected state.",
                    risk_score=finding.risk_score,
                    runbook_id="restart_service",
                    parameters={"service_name": service_name},
                )
            ]

        if finding.resource_type == "file":
            return [
                RemediationAction(
                    finding_id=finding.id,
                    fingerprint=finding.fingerprint,
                    strategy="restore_file_from_baseline",
                    description="File drift requires restore from a trusted artifact store.",
                    risk_score=finding.risk_score,
                )
            ]

        if finding.drift_type == DriftType.ADDED:
            return [
                RemediationAction(
                    finding_id=finding.id,
                    fingerprint=finding.fingerprint,
                    strategy="quarantine_unexpected_resource",
                    description=(
                        "Unexpected resource should be quarantined or removed " "after approval."
                    ),
                    risk_score=finding.risk_score,
                )
            ]

        return [
            RemediationAction(
                finding_id=finding.id,
                fingerprint=finding.fingerprint,
                strategy="manual_review",
                description="No automatic strategy is registered; route to operations review.",
                risk_score=finding.risk_score,
            )
        ]
