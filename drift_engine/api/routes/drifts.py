from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from drift_engine.api.dependencies import request_engine as get_engine
from drift_engine.api.schemas.drift import CollectRequest, DriftReportResponse, DriftRunRequest
from drift_engine.api.security import Scopes, audit_action, require_scope
from drift_engine.collectors.base import CollectionContext
from drift_engine.core.engine import DriftEngine

router = APIRouter(prefix="/drifts", tags=["drifts"])
ENGINE_DEP = Depends(get_engine)
SCAN_EXECUTE = Depends(require_scope(Scopes.SCAN_EXECUTE))


@router.post("/run", response_model=DriftReportResponse, dependencies=[SCAN_EXECUTE])
async def run_drift_scan(
    request: Request,
    payload: DriftRunRequest,
    engine: DriftEngine = ENGINE_DEP,
) -> DriftReportResponse:
    result = await engine.run_once(
        baseline_id=payload.baseline_id,
        collector_names=payload.collector_names,
        auto_remediate=payload.auto_remediate,
        context=CollectionContext(scope=payload.scope),
    )
    await audit_action(
        engine=engine,
        request=request,
        action="drift.scan_executed",
        target_type="drift_report",
        target_id=result.report.id,
        details={
            "baseline_id": payload.baseline_id,
            "collector_names": payload.collector_names,
            "auto_remediate": payload.auto_remediate,
            "risk_score": result.report.risk_score,
        },
    )
    return DriftReportResponse.from_domain(result.report)


@router.get("", response_model=list[DriftReportResponse])
async def list_reports(
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    engine: DriftEngine = ENGINE_DEP,
) -> list[DriftReportResponse]:
    reports = await engine.reports.list(limit=limit, offset=offset)
    return [DriftReportResponse.from_domain(report) for report in reports]


@router.get("/{report_id}", response_model=DriftReportResponse)
async def get_report(
    report_id: str,
    engine: DriftEngine = ENGINE_DEP,
) -> DriftReportResponse:
    report = await engine.reports.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="drift report not found")
    return DriftReportResponse.from_domain(report)


@router.post("/collect", dependencies=[SCAN_EXECUTE])
async def collect_state(
    request: Request,
    payload: CollectRequest,
    engine: DriftEngine = ENGINE_DEP,
) -> dict[str, object]:
    snapshot, results = await engine.collect_state(
        collector_names=payload.collector_names,
        context=CollectionContext(scope=payload.scope),
    )
    await audit_action(
        engine=engine,
        request=request,
        action="state.collected",
        target_type="snapshot",
        target_id=snapshot.id,
        details={"collector_names": payload.collector_names},
    )
    return {
        "snapshot": snapshot.to_document(),
        "collectors": [
            {
                "collector_name": item.collector_name,
                "status": item.status.value,
                "duration_ms": item.duration_ms,
                "errors": item.errors,
            }
            for item in results
        ],
    }
