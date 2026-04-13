from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from drift_engine.api.dependencies import request_engine as get_engine
from drift_engine.api.schemas.baseline import (
    BaselineCreate,
    BaselineFromCurrentRequest,
    BaselineResponse,
)
from drift_engine.api.security import Scopes, audit_action, require_scope
from drift_engine.collectors.base import CollectionContext
from drift_engine.core.engine import DriftEngine

router = APIRouter(prefix="/baselines", tags=["baselines"])
ENGINE_DEP = Depends(get_engine)
BASELINE_WRITE = Depends(require_scope(Scopes.BASELINE_WRITE))


@router.post("", response_model=BaselineResponse, status_code=201, dependencies=[BASELINE_WRITE])
async def create_baseline(
    request: Request,
    payload: BaselineCreate,
    engine: DriftEngine = ENGINE_DEP,
) -> BaselineResponse:
    baseline = engine.baseline_manager.create(
        name=payload.name,
        version=payload.version,
        resources=payload.resources,
        scope=payload.scope,
        metadata=payload.metadata,
    )
    await engine.baselines.save(baseline)
    await audit_action(
        engine=engine,
        request=request,
        action="baseline.created",
        target_type="baseline",
        target_id=baseline.id,
        details={"name": baseline.name, "version": baseline.version},
    )
    return BaselineResponse.from_domain(baseline)


@router.post(
    "/from-current",
    response_model=BaselineResponse,
    status_code=201,
    dependencies=[BASELINE_WRITE],
)
async def create_from_current(
    request: Request,
    payload: BaselineFromCurrentRequest,
    engine: DriftEngine = ENGINE_DEP,
) -> BaselineResponse:
    baseline = await engine.create_baseline_from_current_state(
        name=payload.name,
        version=payload.version,
        collector_names=payload.collector_names,
        context=CollectionContext(scope=payload.scope),
        metadata=payload.metadata,
    )
    await audit_action(
        engine=engine,
        request=request,
        action="baseline.created_from_current",
        target_type="baseline",
        target_id=baseline.id,
        details={
            "name": baseline.name,
            "collector_names": payload.collector_names,
            "scope": payload.scope,
        },
    )
    return BaselineResponse.from_domain(baseline)


@router.get("", response_model=list[BaselineResponse])
async def list_baselines(
    limit: int = 100,
    offset: int = 0,
    engine: DriftEngine = ENGINE_DEP,
) -> list[BaselineResponse]:
    baselines = await engine.baselines.list(limit=limit, offset=offset)
    return [BaselineResponse.from_domain(item) for item in baselines]


@router.get("/{baseline_id}", response_model=BaselineResponse)
async def get_baseline(
    baseline_id: str,
    engine: DriftEngine = ENGINE_DEP,
) -> BaselineResponse:
    baseline = await engine.baselines.get(baseline_id)
    if baseline is None:
        raise HTTPException(status_code=404, detail="baseline not found")
    return BaselineResponse.from_domain(baseline)
