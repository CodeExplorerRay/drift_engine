from __future__ import annotations

import asyncio
import datetime as dt
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from drift_engine.core.models import new_id, utcnow


class RemediationStatus(StrEnum):
    PLANNED = "planned"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    SKIPPED = "skipped"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(slots=True)
class RemediationAction:
    finding_id: str
    fingerprint: str
    strategy: str
    description: str
    risk_score: float
    command: list[str] = field(default_factory=list)
    runbook_id: str | None = None
    parameters: dict[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: new_id("remed"))
    status: RemediationStatus = RemediationStatus.PLANNED
    requires_approval: bool = True
    approved_by: str | None = None
    approval_expires_at: dt.datetime | None = None
    idempotency_key: str | None = None
    dry_run: bool = True
    output: str = ""
    error: str = ""
    created_at: dt.datetime = field(default_factory=utcnow)
    executed_at: dt.datetime | None = None

    def to_document(self) -> dict[str, object]:
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "fingerprint": self.fingerprint,
            "strategy": self.strategy,
            "description": self.description,
            "risk_score": self.risk_score,
            "command": self.command,
            "runbook_id": self.runbook_id,
            "parameters": self.parameters,
            "status": self.status.value,
            "requires_approval": self.requires_approval,
            "approved_by": self.approved_by,
            "approval_expires_at": self.approval_expires_at.isoformat()
            if self.approval_expires_at
            else None,
            "idempotency_key": self.idempotency_key,
            "dry_run": self.dry_run,
            "output": self.output,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


class ActionExecutor(Protocol):
    async def execute(self, action: RemediationAction) -> RemediationAction:
        """Execute a remediation action."""


class NoopExecutor:
    async def execute(self, action: RemediationAction) -> RemediationAction:
        action.status = RemediationStatus.SKIPPED if action.dry_run else RemediationStatus.SUCCEEDED
        action.output = (
            "dry-run noop remediation" if action.dry_run else "noop remediation executed"
        )
        action.executed_at = utcnow()
        return action


class RunbookActionExecutor:
    """Executes named, allow-listed runbook actions only.

    Production deployments should keep dry-run enabled until commands are
    reviewed and restricted to a narrow operational runbook.
    """

    def __init__(
        self,
        runbooks: dict[str, list[str]] | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.runbooks = runbooks or {"restart_service": ["systemctl", "restart", "{service_name}"]}
        self.timeout_seconds = timeout_seconds

    async def execute(self, action: RemediationAction) -> RemediationAction:
        if action.dry_run:
            action.status = RemediationStatus.SKIPPED
            action.output = f"dry-run runbook: {action.runbook_id or action.strategy}"
            action.executed_at = utcnow()
            return action
        command = self._command_for(action)
        if not command:
            action.status = RemediationStatus.FAILED
            action.error = "action has no allow-listed runbook command"
            return action

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            action.status = RemediationStatus.FAILED
            action.error = "command timed out"
            return action

        action.output = stdout.decode("utf-8", errors="replace")
        action.error = stderr.decode("utf-8", errors="replace")
        action.status = (
            RemediationStatus.SUCCEEDED if process.returncode == 0 else RemediationStatus.FAILED
        )
        action.executed_at = utcnow()
        return action

    def _command_for(self, action: RemediationAction) -> list[str]:
        if action.runbook_id is None or action.runbook_id not in self.runbooks:
            return []
        template = self.runbooks[action.runbook_id]
        try:
            return [part.format(**action.parameters) for part in template]
        except KeyError as error:
            action.error = f"missing runbook parameter: {error}"
            return []


ShellActionExecutor = RunbookActionExecutor
