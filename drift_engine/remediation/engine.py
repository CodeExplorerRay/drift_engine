from __future__ import annotations

import datetime as dt

from config.logging_config import get_logger
from drift_engine.core.exceptions import RemediationError
from drift_engine.core.models import DriftReport
from drift_engine.remediation.actions import (
    ActionExecutor,
    NoopExecutor,
    RemediationAction,
    RemediationStatus,
)
from drift_engine.remediation.approval import ApprovalPolicy
from drift_engine.remediation.strategies import RemediationPlan, RemediationStrategyRegistry

logger = get_logger(__name__)


class RemediationEngine:
    def __init__(
        self,
        *,
        strategies: RemediationStrategyRegistry | None = None,
        approval: ApprovalPolicy | None = None,
        executor: ActionExecutor | None = None,
        enabled: bool = False,
        dry_run: bool = True,
    ) -> None:
        self.strategies = strategies or RemediationStrategyRegistry()
        self.approval = approval or ApprovalPolicy()
        self.executor = executor or NoopExecutor()
        self.enabled = enabled
        self.dry_run = dry_run

    @property
    def executor_mode(self) -> str:
        return getattr(self.executor, "mode", self.executor.__class__.__name__.lower())

    @property
    def real_execution_available(self) -> bool:
        return bool(getattr(self.executor, "supports_real_execution", False))

    def capability(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "executor_mode": self.executor_mode,
            "real_execution_available": self.real_execution_available,
            "simulation_only": self.dry_run or not self.real_execution_available,
            "can_execute": self.enabled and (self.dry_run or self.real_execution_available),
        }

    def plan(self, report: DriftReport) -> RemediationPlan:
        plan = self.strategies.plan(report)
        for action in plan.actions:
            action.dry_run = self.dry_run
            action.executor_mode = self.executor_mode
            action.simulated = self.dry_run or not self.real_execution_available
            self.approval.apply(action)
        return plan

    async def execute(self, plan: RemediationPlan) -> list[RemediationAction]:
        if not self.enabled:
            raise RemediationError("remediation execution is disabled")
        if not self.dry_run and not self.real_execution_available:
            raise RemediationError("real remediation executor is not configured")

        executed: list[RemediationAction] = []
        for action in plan.actions:
            action.executor_mode = self.executor_mode
            action.simulated = self.dry_run or not self.real_execution_available
            if not action.dry_run and action.approved_by is None:
                action.status = RemediationStatus.WAITING_APPROVAL
                action.requires_approval = True
                action.error = "explicit approval is required for non-dry-run remediation"
                executed.append(action)
                continue
            if action.requires_approval or action.status == RemediationStatus.WAITING_APPROVAL:
                logger.info("remediation_waiting_approval", action_id=action.id)
                executed.append(action)
                continue
            if action.approval_expires_at and action.approval_expires_at <= dt.datetime.now(dt.UTC):
                action.status = RemediationStatus.WAITING_APPROVAL
                action.requires_approval = True
                action.error = "approval expired"
                executed.append(action)
                continue
            executed.append(await self.executor.execute(action))
        return executed
