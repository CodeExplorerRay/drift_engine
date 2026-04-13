from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod
from collections.abc import Iterable

from drift_engine.core.models import Baseline, DriftReport, StateSnapshot
from drift_engine.core.operations import AuditEvent, JobRun, ScheduledScanJob
from drift_engine.policies.models import PolicyRule
from drift_engine.remediation.actions import RemediationAction
from drift_engine.remediation.strategies import RemediationPlan


class BaselineRepository(ABC):
    @abstractmethod
    async def save(self, baseline: Baseline) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, baseline_id: str) -> Baseline | None:
        raise NotImplementedError

    @abstractmethod
    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Baseline]:
        raise NotImplementedError


class SnapshotRepository(ABC):
    @abstractmethod
    async def save(self, snapshot: StateSnapshot) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, snapshot_id: str) -> StateSnapshot | None:
        raise NotImplementedError


class DriftReportRepository(ABC):
    @abstractmethod
    async def save(self, report: DriftReport) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, report_id: str) -> DriftReport | None:
        raise NotImplementedError

    @abstractmethod
    async def list(self, *, limit: int = 100, offset: int = 0) -> list[DriftReport]:
        raise NotImplementedError


class PolicyRepository(ABC):
    @abstractmethod
    async def save(self, policy: PolicyRule) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> list[PolicyRule]:
        raise NotImplementedError


class AuditRepository(ABC):
    @abstractmethod
    async def save(self, event: AuditEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list(self, *, limit: int = 100, offset: int = 0) -> list[AuditEvent]:
        raise NotImplementedError


class JobRepository(ABC):
    @abstractmethod
    async def save_job(self, job: ScheduledScanJob) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_job(self, job_id: str) -> ScheduledScanJob | None:
        raise NotImplementedError

    @abstractmethod
    async def list_jobs(self, *, include_disabled: bool = False) -> list[ScheduledScanJob]:
        raise NotImplementedError

    @abstractmethod
    async def list_due_jobs(self, now: dt.datetime) -> list[ScheduledScanJob]:
        raise NotImplementedError

    @abstractmethod
    async def save_run(self, run: JobRun) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_runs(self, *, job_id: str | None = None, limit: int = 100) -> list[JobRun]:
        raise NotImplementedError

    @abstractmethod
    async def acquire_lock(self, name: str, owner: str, ttl_seconds: int) -> bool:
        raise NotImplementedError


class RemediationRepository(ABC):
    @abstractmethod
    async def save_plan(self, plan: RemediationPlan) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_action(self, action_id: str) -> RemediationAction | None:
        raise NotImplementedError

    @abstractmethod
    async def save_action(self, action: RemediationAction) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_actions(
        self, *, report_id: str | None = None, limit: int = 100
    ) -> list[RemediationAction]:
        raise NotImplementedError


class InMemoryBaselineRepository(BaselineRepository):
    def __init__(self, baselines: Iterable[Baseline] | None = None) -> None:
        self._items = {item.id: item for item in baselines or []}

    async def save(self, baseline: Baseline) -> None:
        self._items[baseline.id] = baseline

    async def get(self, baseline_id: str) -> Baseline | None:
        return self._items.get(baseline_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Baseline]:
        return list(self._items.values())[offset : offset + limit]


class InMemorySnapshotRepository(SnapshotRepository):
    def __init__(self) -> None:
        self._items: dict[str, StateSnapshot] = {}

    async def save(self, snapshot: StateSnapshot) -> None:
        self._items[snapshot.id] = snapshot

    async def get(self, snapshot_id: str) -> StateSnapshot | None:
        return self._items.get(snapshot_id)


class InMemoryDriftReportRepository(DriftReportRepository):
    def __init__(self) -> None:
        self._items: dict[str, DriftReport] = {}

    async def save(self, report: DriftReport) -> None:
        self._items[report.id] = report

    async def get(self, report_id: str) -> DriftReport | None:
        return self._items.get(report_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[DriftReport]:
        reports = sorted(self._items.values(), key=lambda item: item.generated_at, reverse=True)
        return reports[offset : offset + limit]


class InMemoryPolicyRepository(PolicyRepository):
    def __init__(self, policies: Iterable[PolicyRule] | None = None) -> None:
        self._items = {policy.id: policy for policy in policies or []}

    async def save(self, policy: PolicyRule) -> None:
        self._items[policy.id] = policy

    async def list(self) -> list[PolicyRule]:
        return list(self._items.values())


class InMemoryAuditRepository(AuditRepository):
    def __init__(self) -> None:
        self._items: dict[str, AuditEvent] = {}

    async def save(self, event: AuditEvent) -> None:
        self._items[event.id] = event

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[AuditEvent]:
        events = sorted(self._items.values(), key=lambda item: item.created_at, reverse=True)
        return events[offset : offset + limit]


class InMemoryJobRepository(JobRepository):
    def __init__(self) -> None:
        self._jobs: dict[str, ScheduledScanJob] = {}
        self._runs: dict[str, JobRun] = {}
        self._locks: dict[str, tuple[str, dt.datetime]] = {}

    async def save_job(self, job: ScheduledScanJob) -> None:
        self._jobs[job.id] = job

    async def get_job(self, job_id: str) -> ScheduledScanJob | None:
        return self._jobs.get(job_id)

    async def list_jobs(self, *, include_disabled: bool = False) -> list[ScheduledScanJob]:
        jobs = list(self._jobs.values())
        if not include_disabled:
            jobs = [job for job in jobs if job.enabled]
        return sorted(jobs, key=lambda item: item.created_at, reverse=True)

    async def list_due_jobs(self, now: dt.datetime) -> list[ScheduledScanJob]:
        return [
            job
            for job in await self.list_jobs()
            if job.enabled and job.next_run_at <= now
        ]

    async def save_run(self, run: JobRun) -> None:
        self._runs[run.id] = run

    async def list_runs(self, *, job_id: str | None = None, limit: int = 100) -> list[JobRun]:
        runs = list(self._runs.values())
        if job_id:
            runs = [run for run in runs if run.job_id == job_id]
        return sorted(runs, key=lambda item: item.started_at, reverse=True)[:limit]

    async def acquire_lock(self, name: str, owner: str, ttl_seconds: int) -> bool:
        now = dt.datetime.now(dt.UTC)
        current = self._locks.get(name)
        if current and current[1] > now:
            return current[0] == owner
        self._locks[name] = (owner, now + dt.timedelta(seconds=ttl_seconds))
        return True


class InMemoryRemediationRepository(RemediationRepository):
    def __init__(self) -> None:
        self._actions: dict[str, RemediationAction] = {}
        self._action_report: dict[str, str] = {}

    async def save_plan(self, plan: RemediationPlan) -> None:
        for action in plan.actions:
            self._actions[action.id] = action
            self._action_report[action.id] = plan.report_id

    async def get_action(self, action_id: str) -> RemediationAction | None:
        return self._actions.get(action_id)

    async def save_action(self, action: RemediationAction) -> None:
        self._actions[action.id] = action

    async def list_actions(
        self, *, report_id: str | None = None, limit: int = 100
    ) -> list[RemediationAction]:
        actions = list(self._actions.values())
        if report_id is not None:
            actions = [
                action for action in actions if self._action_report.get(action.id) == report_id
            ]
        return sorted(actions, key=lambda item: item.created_at, reverse=True)[:limit]
