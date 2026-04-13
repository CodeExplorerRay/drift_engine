from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from drift_engine.api.dependencies import request_engine as get_engine
from drift_engine.api.schemas.policy import PolicyRuleCreate, PolicyRuleResponse
from drift_engine.api.security import Scopes, audit_action, require_scope
from drift_engine.core.engine import DriftEngine

router = APIRouter(prefix="/policies", tags=["policies"])
ENGINE_DEP = Depends(get_engine)
POLICY_WRITE = Depends(require_scope(Scopes.POLICY_WRITE))


@router.get("", response_model=list[PolicyRuleResponse])
async def list_policies(engine: DriftEngine = ENGINE_DEP) -> list[PolicyRuleResponse]:
    return [PolicyRuleResponse.from_domain(rule) for rule in engine.policies.rules]


@router.post("", response_model=PolicyRuleResponse, status_code=201, dependencies=[POLICY_WRITE])
async def create_policy(
    request: Request,
    payload: PolicyRuleCreate,
    engine: DriftEngine = ENGINE_DEP,
) -> PolicyRuleResponse:
    rule = payload.to_domain()
    engine.policies.add_rule(rule)
    if engine.policy_repository is not None:
        await engine.policy_repository.save(rule)
    await audit_action(
        engine=engine,
        request=request,
        action="policy.created",
        target_type="policy",
        target_id=rule.id,
        details={"name": rule.name, "effect": rule.effect.value, "severity": rule.severity.value},
    )
    return PolicyRuleResponse.from_domain(rule)
