from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from drift_engine.core.operations import JobRun, ScheduledScanJob


class ScheduledJobCreate(BaseModel):
    name: str = Field(min_length=1)
    baseline_id: str
    interval_seconds: int = Field(ge=1)
    collector_names: list[str] | None = None
    enabled: bool = True
    next_run_at: dt.datetime | None = None


class ScheduledJobResponse(BaseModel):
    id: str
    name: str
    baseline_id: str
    collector_names: list[str] | None
    interval_seconds: int
    enabled: bool
    created_at: str
    updated_at: str
    next_run_at: str
    last_run_at: str | None

    @classmethod
    def from_domain(cls, job: ScheduledScanJob) -> ScheduledJobResponse:
        return cls(**job.to_document())


class JobRunResponse(BaseModel):
    id: str
    job_id: str
    status: str
    report_id: str | None
    error: str
    started_at: str
    finished_at: str | None

    @classmethod
    def from_domain(cls, run: JobRun) -> JobRunResponse:
        return cls(**run.to_document())
