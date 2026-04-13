from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from drift_engine.api.dependencies import request_engine as get_engine
from drift_engine.api.security import Scopes, audit_action, request_principal, require_scope
from drift_engine.core.engine import DriftEngine
from drift_engine.remediation.actions import RemediationStatus
from drift_engine.remediation.strategies import RemediationPlan

router = APIRouter(prefix="/remediation", tags=["remediation"])
ENGINE_DEP = Depends(get_engine)
REMEDIATION_PLAN = Depends(require_scope(Scopes.REMEDIATION_PLAN))
REMEDIATION_APPROVE = Depends(require_scope(Scopes.REMEDIATION_APPROVE))
REMEDIATION_EXECUTE = Depends(require_scope(Scopes.REMEDIATION_EXECUTE))


class RemediationApprovalRequest(BaseModel):
    expires_in_seconds: int = Field(default=3600, ge=60, le=86_400)


@router.post("/reports/{report_id}/plan", dependencies=[REMEDIATION_PLAN])
async def plan_remediation(
    request: Request,
    report_id: str,
    engine: DriftEngine = ENGINE_DEP,
) -> dict[str, object]:
    report = await engine.reports.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="drift report not found")
    if engine.remediation is None:
        raise HTTPException(status_code=400, detail="remediation engine is not configured")
    if engine.remediation_repository is not None:
        existing = await engine.remediation_repository.list_actions(report_id=report_id)
        if existing:
            return {
                "report_id": report_id,
                "existing": True,
                "actions": [action.to_document() for action in existing],
            }
    plan = engine.remediation.plan(report)
    if engine.remediation_repository is not None:
        await engine.remediation_repository.save_plan(plan)
    await audit_action(
        engine=engine,
        request=request,
        action="remediation.plan_created",
        target_type="drift_report",
        target_id=report_id,
        details={"actions": len(plan.actions)},
    )
    return plan.to_document()


@router.get("/actions")
async def list_actions(
    report_id: str | None = None,
    limit: int = 100,
    engine: DriftEngine = ENGINE_DEP,
) -> list[dict[str, object]]:
    if engine.remediation_repository is None:
        raise HTTPException(status_code=501, detail="remediation repository is not configured")
    actions = await engine.remediation_repository.list_actions(report_id=report_id, limit=limit)
    return [action.to_document() for action in actions]


@router.post("/actions/{action_id}/approve", dependencies=[REMEDIATION_APPROVE])
async def approve_action(
    request: Request,
    action_id: str,
    payload: RemediationApprovalRequest,
    engine: DriftEngine = ENGINE_DEP,
) -> dict[str, object]:
    if engine.remediation is None:
        raise HTTPException(status_code=400, detail="remediation engine is not configured")
    if engine.remediation_repository is None:
        raise HTTPException(status_code=501, detail="remediation repository is not configured")
    action = await engine.remediation_repository.get_action(action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="remediation action not found")
    principal = request_principal(request)
    expires_at = dt.datetime.now(dt.UTC) + dt.timedelta(seconds=payload.expires_in_seconds)
    engine.remediation.approval.approve(action, approved_by=principal.id, expires_at=expires_at)
    await engine.remediation_repository.save_action(action)
    await audit_action(
        engine=engine,
        request=request,
        action="remediation.action_approved",
        target_type="remediation_action",
        target_id=action.id,
        details={"expires_at": expires_at.isoformat()},
    )
    return action.to_document()


@router.post("/reports/{report_id}/execute", dependencies=[REMEDIATION_EXECUTE])
async def execute_remediation(
    request: Request,
    report_id: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    engine: DriftEngine = ENGINE_DEP,
) -> list[dict[str, object]]:
    report = await engine.reports.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="drift report not found")
    if engine.remediation is None:
        raise HTTPException(status_code=400, detail="remediation engine is not configured")
    if engine.remediation_repository is not None:
        actions = await engine.remediation_repository.list_actions(report_id=report_id)
        if idempotency_key and any(
            action.idempotency_key == idempotency_key
            and action.status
            in {
                RemediationStatus.SKIPPED,
                RemediationStatus.SUCCEEDED,
                RemediationStatus.FAILED,
            }
            for action in actions
        ):
            return [action.to_document() for action in actions]
        if actions:
            plan = RemediationPlan(report_id=report_id, actions=actions)
        else:
            plan = engine.remediation.plan(report)
            await engine.remediation_repository.save_plan(plan)
    else:
        plan = engine.remediation.plan(report)
    for action in plan.actions:
        action.idempotency_key = action.idempotency_key or idempotency_key
    execution = await engine.remediation.execute(plan)
    if engine.remediation_repository is not None:
        for action in execution:
            await engine.remediation_repository.save_action(action)
    await audit_action(
        engine=engine,
        request=request,
        action="remediation.execution_requested",
        target_type="drift_report",
        target_id=report_id,
        details={
            "actions": len(execution),
            "idempotency_key": idempotency_key,
            "statuses": [action.status.value for action in execution],
        },
    )
    return [action.to_document() for action in execution]
