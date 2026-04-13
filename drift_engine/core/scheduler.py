from __future__ import annotations

import asyncio
import datetime as dt
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from config.logging_config import get_logger
from drift_engine.core.engine import DriftEngine
from drift_engine.core.operations import JobRun, JobRunStatus, ScheduledScanJob

logger = get_logger(__name__)


@dataclass(slots=True)
class ScheduledJob:
    name: str
    interval_seconds: int
    callback: Callable[[], Awaitable[object]]


class AsyncIntervalScheduler:
    """Lightweight async scheduler used when APScheduler is not required."""

    def __init__(self) -> None:
        self._jobs: list[ScheduledJob] = []
        self._tasks: list[asyncio.Task[object]] = []
        self._stopping = asyncio.Event()

    def add_job(self, job: ScheduledJob) -> None:
        if job.interval_seconds < 1:
            raise ValueError("job interval must be at least one second")
        self._jobs.append(job)

    async def start(self) -> None:
        self._stopping.clear()
        self._tasks = [
            asyncio.create_task(self._run(job), name=f"scheduler:{job.name}") for job in self._jobs
        ]

    async def stop(self) -> None:
        self._stopping.set()
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def _run(self, job: ScheduledJob) -> None:
        while not self._stopping.is_set():
            try:
                await job.callback()
            except asyncio.CancelledError:
                raise
            except Exception as error:
                logger.exception("scheduled_job_failed", job=job.name, error=str(error))
            try:
                await asyncio.wait_for(self._stopping.wait(), timeout=job.interval_seconds)
            except TimeoutError:
                continue


async def execute_scheduled_job(
    *,
    engine: DriftEngine,
    job: ScheduledScanJob,
    owner_id: str,
    lock_ttl_seconds: int,
) -> JobRun:
    if engine.job_repository is None:
        raise RuntimeError("job repository is not configured")

    lock_name = f"scheduled-scan:{job.id}"
    acquired = await engine.job_repository.acquire_lock(lock_name, owner_id, lock_ttl_seconds)
    if not acquired:
        run = JobRun(
            job_id=job.id,
            status=JobRunStatus.SKIPPED,
            error="another scheduler replica owns the lock",
            finished_at=dt.datetime.now(dt.UTC),
        )
        await engine.job_repository.save_run(run)
        return run

    run = JobRun(job_id=job.id)
    await engine.job_repository.save_run(run)
    try:
        result = await engine.run_once(
            baseline_id=job.baseline_id,
            collector_names=job.collector_names,
        )
        run.status = JobRunStatus.SUCCEEDED
        run.report_id = result.report.id
    except Exception as error:
        logger.exception("scheduled_scan_failed", job_id=job.id, error=str(error))
        run.status = JobRunStatus.FAILED
        run.error = str(error)
    finally:
        run.finished_at = dt.datetime.now(dt.UTC)
        await engine.job_repository.save_run(run)
        job.last_run_at = run.finished_at
        job.next_run_at = run.finished_at + dt.timedelta(seconds=job.interval_seconds)
        await engine.job_repository.save_job(job)
    return run


class DriftJobScheduler:
    """Durable scheduled scan dispatcher with repository-backed locking."""

    def __init__(
        self,
        *,
        engine: DriftEngine,
        tick_seconds: int,
        owner_id: str,
        lock_ttl_seconds: int,
    ) -> None:
        self.engine = engine
        self.tick_seconds = max(1, tick_seconds)
        self.owner_id = owner_id
        self.lock_ttl_seconds = max(1, lock_ttl_seconds)
        self._scheduler = AsyncIntervalScheduler()
        self._scheduler.add_job(
            ScheduledJob(
                name="scheduled-scan-dispatcher",
                interval_seconds=self.tick_seconds,
                callback=self.run_due_once,
            )
        )

    async def start(self) -> None:
        await self._scheduler.start()

    async def stop(self) -> None:
        await self._scheduler.stop()

    async def run_due_once(self) -> int:
        if self.engine.job_repository is None:
            return 0
        due_jobs = await self.engine.job_repository.list_due_jobs(dt.datetime.now(dt.UTC))
        for job in due_jobs:
            await execute_scheduled_job(
                engine=self.engine,
                job=job,
                owner_id=self.owner_id,
                lock_ttl_seconds=self.lock_ttl_seconds,
            )
        return len(due_jobs)
