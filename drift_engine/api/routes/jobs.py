from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Request

from drift_engine.api.dependencies import request_engine as get_engine
from drift_engine.api.schemas.jobs import (
    JobRunResponse,
    ScheduledJobCreate,
    ScheduledJobResponse,
)
from drift_engine.api.security import Scopes, audit_action, require_scope
from drift_engine.core.engine import DriftEngine
from drift_engine.core.operations import ScheduledScanJob
from drift_engine.core.scheduler import execute_scheduled_job

router = APIRouter(prefix="/jobs", tags=["jobs"])
ENGINE_DEP = Depends(get_engine)
JOB_WRITE = Depends(require_scope(Scopes.JOB_WRITE))
SCAN_EXECUTE = Depends(require_scope(Scopes.SCAN_EXECUTE))


@router.get("", response_model=list[ScheduledJobResponse])
async def list_jobs(
    include_disabled: bool = True,
    engine: DriftEngine = ENGINE_DEP,
) -> list[ScheduledJobResponse]:
    if engine.job_repository is None:
        raise HTTPException(status_code=501, detail="job repository is not configured")
    jobs = await engine.job_repository.list_jobs(include_disabled=include_disabled)
    return [ScheduledJobResponse.from_domain(job) for job in jobs]


@router.post("", response_model=ScheduledJobResponse, status_code=201, dependencies=[JOB_WRITE])
async def create_job(
    request: Request,
    payload: ScheduledJobCreate,
    engine: DriftEngine = ENGINE_DEP,
) -> ScheduledJobResponse:
    if engine.job_repository is None:
        raise HTTPException(status_code=501, detail="job repository is not configured")
    baseline = await engine.baselines.get(payload.baseline_id)
    if baseline is None:
        raise HTTPException(status_code=404, detail="baseline not found")
    job = ScheduledScanJob(
        name=payload.name,
        baseline_id=payload.baseline_id,
        interval_seconds=payload.interval_seconds,
        collector_names=payload.collector_names,
        enabled=payload.enabled,
        next_run_at=payload.next_run_at or dt.datetime.now(dt.UTC),
    )
    await engine.job_repository.save_job(job)
    await audit_action(
        engine=engine,
        request=request,
        action="job.created",
        target_type="scheduled_job",
        target_id=job.id,
        details={"baseline_id": job.baseline_id, "interval_seconds": job.interval_seconds},
    )
    return ScheduledJobResponse.from_domain(job)


@router.get("/runs", response_model=list[JobRunResponse])
async def list_runs(
    job_id: str | None = None,
    limit: int = 100,
    engine: DriftEngine = ENGINE_DEP,
) -> list[JobRunResponse]:
    if engine.job_repository is None:
        raise HTTPException(status_code=501, detail="job repository is not configured")
    runs = await engine.job_repository.list_runs(job_id=job_id, limit=limit)
    return [JobRunResponse.from_domain(run) for run in runs]


@router.post("/{job_id}/run", response_model=JobRunResponse, dependencies=[SCAN_EXECUTE])
async def run_job_now(
    request: Request,
    job_id: str,
    engine: DriftEngine = ENGINE_DEP,
) -> JobRunResponse:
    if engine.job_repository is None:
        raise HTTPException(status_code=501, detail="job repository is not configured")
    job = await engine.job_repository.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    run = await execute_scheduled_job(
        engine=engine,
        job=job,
        owner_id="manual-api",
        lock_ttl_seconds=max(60, job.interval_seconds),
    )
    await audit_action(
        engine=engine,
        request=request,
        action="job.manual_run",
        target_type="scheduled_job",
        target_id=job.id,
        details={"run_id": run.id, "status": run.status.value, "report_id": run.report_id},
    )
    return JobRunResponse.from_domain(run)
