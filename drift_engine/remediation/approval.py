from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from drift_engine.remediation.actions import RemediationAction, RemediationStatus


@dataclass(slots=True)
class ApprovalPolicy:
    auto_approve_below_risk: float = 20.0
    require_approval_for_runbooks: bool = True

    def apply(self, action: RemediationAction) -> RemediationAction:
        action.requires_approval = action.risk_score >= self.auto_approve_below_risk or (
            self.require_approval_for_runbooks and bool(action.runbook_id)
        )
        action.status = (
            RemediationStatus.WAITING_APPROVAL
            if action.requires_approval
            else RemediationStatus.APPROVED
        )
        return action

    def approve(
        self,
        action: RemediationAction,
        approved_by: str,
        expires_at: dt.datetime | None = None,
    ) -> RemediationAction:
        action.approved_by = approved_by
        action.approval_expires_at = expires_at
        action.requires_approval = False
        action.status = RemediationStatus.APPROVED
        return action
