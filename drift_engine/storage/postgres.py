from __future__ import annotations

import datetime as dt
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from drift_engine.core.models import (
    Baseline,
    DriftFinding,
    DriftReport,
    DriftStatus,
    DriftSummary,
    DriftType,
    ScanCompleteness,
    Severity,
    StateSnapshot,
    new_id,
)
from drift_engine.core.operations import AuditEvent, JobRun, ScheduledScanJob
from drift_engine.policies.models import PolicyCondition, PolicyEffect, PolicyRule, RuleOperator
from drift_engine.remediation.actions import RemediationAction, RemediationStatus
from drift_engine.remediation.strategies import RemediationPlan
from drift_engine.storage.base import (
    AuditRepository,
    BaselineRepository,
    DriftReportRepository,
    JobRepository,
    PolicyRepository,
    RemediationRepository,
    SnapshotRepository,
)

metadata = sa.MetaData()

json_type = JSONB().with_variant(sa.JSON(), "sqlite")  # type: ignore[no-untyped-call]

baselines_table = sa.Table(
    "baselines",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("name", sa.String(255), nullable=False),
    sa.Column("version", sa.String(64), nullable=False),
    sa.Column("checksum", sa.String(128), nullable=False),
    sa.Column("document", json_type, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)

snapshots_table = sa.Table(
    "snapshots",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("source", sa.String(255), nullable=False),
    sa.Column("checksum", sa.String(128), nullable=False),
    sa.Column("document", json_type, nullable=False),
    sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
)

drift_reports_table = sa.Table(
    "drift_reports",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("baseline_id", sa.String(64), nullable=False),
    sa.Column("snapshot_id", sa.String(64), nullable=False),
    sa.Column("risk_score", sa.Float, nullable=False),
    sa.Column("document", json_type, nullable=False),
    sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
)

policies_table = sa.Table(
    "policies",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("name", sa.String(255), nullable=False),
    sa.Column("enabled", sa.Boolean, nullable=False),
    sa.Column("document", json_type, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)

audit_events_table = sa.Table(
    "audit_events",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("action", sa.String(128), nullable=False),
    sa.Column("actor_id", sa.String(255), nullable=False),
    sa.Column("target_type", sa.String(128), nullable=False),
    sa.Column("target_id", sa.String(255), nullable=False),
    sa.Column("document", json_type, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)

scheduled_jobs_table = sa.Table(
    "scheduled_jobs",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("name", sa.String(255), nullable=False),
    sa.Column("baseline_id", sa.String(64), nullable=False),
    sa.Column("enabled", sa.Boolean, nullable=False),
    sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("document", json_type, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)

job_runs_table = sa.Table(
    "job_runs",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("job_id", sa.String(64), nullable=False),
    sa.Column("status", sa.String(32), nullable=False),
    sa.Column("document", json_type, nullable=False),
    sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
)

scheduler_locks_table = sa.Table(
    "scheduler_locks",
    metadata,
    sa.Column("name", sa.String(255), primary_key=True),
    sa.Column("owner", sa.String(255), nullable=False),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
)

remediation_plans_table = sa.Table(
    "remediation_plans",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("report_id", sa.String(64), nullable=False),
    sa.Column("document", json_type, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)

remediation_actions_table = sa.Table(
    "remediation_actions",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("plan_id", sa.String(64), nullable=False),
    sa.Column("report_id", sa.String(64), nullable=False),
    sa.Column("status", sa.String(32), nullable=False),
    sa.Column("fingerprint", sa.String(128), nullable=False),
    sa.Column("idempotency_key", sa.String(255), nullable=True),
    sa.Column("document", json_type, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)

remediation_executions_table = sa.Table(
    "remediation_executions",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("report_id", sa.String(64), nullable=False),
    sa.Column("idempotency_key", sa.String(255), nullable=False),
    sa.Column("status", sa.String(32), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)

sa.Index(
    "ix_baselines_name_version",
    baselines_table.c.name,
    baselines_table.c.version,
    unique=True,
)
sa.Index(
    "ix_snapshots_source_collected_at",
    snapshots_table.c.source,
    snapshots_table.c.collected_at,
)
sa.Index("ix_drift_reports_baseline_id", drift_reports_table.c.baseline_id)
sa.Index("ix_drift_reports_generated_at", drift_reports_table.c.generated_at)
sa.Index("ix_audit_events_created_at", audit_events_table.c.created_at)
sa.Index("ix_audit_events_target", audit_events_table.c.target_type, audit_events_table.c.target_id)
sa.Index(
    "ix_scheduled_jobs_due",
    scheduled_jobs_table.c.enabled,
    scheduled_jobs_table.c.next_run_at,
)
sa.Index("ix_job_runs_job_started", job_runs_table.c.job_id, job_runs_table.c.started_at)
sa.Index("ix_remediation_plans_report", remediation_plans_table.c.report_id)
sa.Index("ix_remediation_actions_report", remediation_actions_table.c.report_id)
sa.Index("ix_remediation_actions_idempotency", remediation_actions_table.c.idempotency_key)
sa.Index(
    "ux_remediation_actions_report_fingerprint",
    remediation_actions_table.c.report_id,
    remediation_actions_table.c.fingerprint,
    unique=True,
)
sa.Index(
    "ux_remediation_executions_idempotency",
    remediation_executions_table.c.idempotency_key,
    unique=True,
)


def build_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_pre_ping=True)


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def create_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(metadata.create_all)


async def check_database(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        await connection.execute(sa.text("SELECT 1"))
        await connection.execute(sa.select(baselines_table.c.id).limit(1))


class PostgresBaselineRepository(BaselineRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def save(self, baseline: Baseline) -> None:
        now = dt.datetime.now(dt.UTC)
        document = baseline.to_document()
        async with self.session_factory() as session:
            async with session.begin():
                exists = await session.scalar(
                    sa.select(baselines_table.c.id).where(baselines_table.c.id == baseline.id)
                )
                statement = (
                    sa.update(baselines_table)
                    .where(baselines_table.c.id == baseline.id)
                    .values(
                        name=baseline.name,
                        version=baseline.version,
                        checksum=baseline.checksum,
                        document=document,
                        updated_at=now,
                    )
                    if exists
                    else sa.insert(baselines_table).values(
                        id=baseline.id,
                        name=baseline.name,
                        version=baseline.version,
                        checksum=baseline.checksum,
                        document=document,
                        created_at=baseline.created_at,
                        updated_at=now,
                    )
                )
                await session.execute(statement)

    async def get(self, baseline_id: str) -> Baseline | None:
        async with self.session_factory() as session:
            row = (
                await session.execute(
                    sa.select(baselines_table.c.document).where(baselines_table.c.id == baseline_id)
                )
            ).first()
        return Baseline.from_document(row[0]) if row else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Baseline]:
        async with self.session_factory() as session:
            rows = (
                await session.execute(
                    sa.select(baselines_table.c.document)
                    .order_by(baselines_table.c.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            ).all()
        return [Baseline.from_document(row[0]) for row in rows]


class PostgresSnapshotRepository(SnapshotRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def save(self, snapshot: StateSnapshot) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(
                    sa.insert(snapshots_table).values(
                        id=snapshot.id,
                        source=snapshot.source,
                        checksum=snapshot.checksum,
                        document=snapshot.to_document(),
                        collected_at=snapshot.collected_at,
                    )
                )

    async def get(self, snapshot_id: str) -> StateSnapshot | None:
        async with self.session_factory() as session:
            row = (
                await session.execute(
                    sa.select(snapshots_table.c.document).where(snapshots_table.c.id == snapshot_id)
                )
            ).first()
        return StateSnapshot.from_document(row[0]) if row else None


class PostgresDriftReportRepository(DriftReportRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def save(self, report: DriftReport) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(
                    sa.insert(drift_reports_table).values(
                        id=report.id,
                        baseline_id=report.baseline_id,
                        snapshot_id=report.snapshot_id,
                        risk_score=report.risk_score,
                        document=report.to_document(),
                        generated_at=report.generated_at,
                    )
                )

    async def get(self, report_id: str) -> DriftReport | None:
        async with self.session_factory() as session:
            row = (
                await session.execute(
                    sa.select(drift_reports_table.c.document).where(
                        drift_reports_table.c.id == report_id
                    )
                )
            ).first()
        return _report_from_document(row[0]) if row else None

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[DriftReport]:
        async with self.session_factory() as session:
            rows = (
                await session.execute(
                    sa.select(drift_reports_table.c.document)
                    .order_by(drift_reports_table.c.generated_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            ).all()
        return [_report_from_document(row[0]) for row in rows]


class PostgresPolicyRepository(PolicyRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def save(self, policy: PolicyRule) -> None:
        now = dt.datetime.now(dt.UTC)
        document = policy.to_document()
        async with self.session_factory() as session:
            async with session.begin():
                exists = await session.scalar(
                    sa.select(policies_table.c.id).where(policies_table.c.id == policy.id)
                )
                statement = (
                    sa.update(policies_table)
                    .where(policies_table.c.id == policy.id)
                    .values(
                        name=policy.name,
                        enabled=policy.enabled,
                        document=document,
                        updated_at=now,
                    )
                    if exists
                    else sa.insert(policies_table).values(
                        id=policy.id,
                        name=policy.name,
                        enabled=policy.enabled,
                        document=document,
                        created_at=policy.created_at,
                        updated_at=now,
                    )
                )
                await session.execute(statement)

    async def list(self) -> list[PolicyRule]:
        async with self.session_factory() as session:
            rows = (
                await session.execute(
                    sa.select(policies_table.c.document).order_by(policies_table.c.created_at.desc())
                )
            ).all()
        return [_policy_from_document(row[0]) for row in rows]


class PostgresAuditRepository(AuditRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def save(self, event: AuditEvent) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(
                    sa.insert(audit_events_table).values(
                        id=event.id,
                        action=event.action,
                        actor_id=event.actor_id,
                        target_type=event.target_type,
                        target_id=event.target_id,
                        document=event.to_document(),
                        created_at=event.created_at,
                    )
                )

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[AuditEvent]:
        async with self.session_factory() as session:
            rows = (
                await session.execute(
                    sa.select(audit_events_table.c.document)
                    .order_by(audit_events_table.c.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            ).all()
        return [AuditEvent.from_document(row[0]) for row in rows]


class PostgresJobRepository(JobRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def save_job(self, job: ScheduledScanJob) -> None:
        now = dt.datetime.now(dt.UTC)
        job.updated_at = now
        document = job.to_document()
        async with self.session_factory() as session:
            async with session.begin():
                exists = await session.scalar(
                    sa.select(scheduled_jobs_table.c.id).where(scheduled_jobs_table.c.id == job.id)
                )
                statement = (
                    sa.update(scheduled_jobs_table)
                    .where(scheduled_jobs_table.c.id == job.id)
                    .values(
                        name=job.name,
                        baseline_id=job.baseline_id,
                        enabled=job.enabled,
                        next_run_at=job.next_run_at,
                        document=document,
                        updated_at=now,
                    )
                    if exists
                    else sa.insert(scheduled_jobs_table).values(
                        id=job.id,
                        name=job.name,
                        baseline_id=job.baseline_id,
                        enabled=job.enabled,
                        next_run_at=job.next_run_at,
                        document=document,
                        created_at=job.created_at,
                        updated_at=now,
                    )
                )
                await session.execute(statement)

    async def get_job(self, job_id: str) -> ScheduledScanJob | None:
        async with self.session_factory() as session:
            row = (
                await session.execute(
                    sa.select(scheduled_jobs_table.c.document).where(
                        scheduled_jobs_table.c.id == job_id
                    )
                )
            ).first()
        return ScheduledScanJob.from_document(row[0]) if row else None

    async def list_jobs(self, *, include_disabled: bool = False) -> list[ScheduledScanJob]:
        statement = sa.select(scheduled_jobs_table.c.document).order_by(
            scheduled_jobs_table.c.created_at.desc()
        )
        if not include_disabled:
            statement = statement.where(scheduled_jobs_table.c.enabled.is_(True))
        async with self.session_factory() as session:
            rows = (await session.execute(statement)).all()
        return [ScheduledScanJob.from_document(row[0]) for row in rows]

    async def list_due_jobs(self, now: dt.datetime) -> list[ScheduledScanJob]:
        async with self.session_factory() as session:
            rows = (
                await session.execute(
                    sa.select(scheduled_jobs_table.c.document)
                    .where(scheduled_jobs_table.c.enabled.is_(True))
                    .where(scheduled_jobs_table.c.next_run_at <= now)
                    .order_by(scheduled_jobs_table.c.next_run_at.asc())
                )
            ).all()
        return [ScheduledScanJob.from_document(row[0]) for row in rows]

    async def save_run(self, run: JobRun) -> None:
        document = run.to_document()
        async with self.session_factory() as session:
            async with session.begin():
                exists = await session.scalar(
                    sa.select(job_runs_table.c.id).where(job_runs_table.c.id == run.id)
                )
                statement = (
                    sa.update(job_runs_table)
                    .where(job_runs_table.c.id == run.id)
                    .values(
                        status=run.status.value,
                        document=document,
                        finished_at=run.finished_at,
                    )
                    if exists
                    else sa.insert(job_runs_table).values(
                        id=run.id,
                        job_id=run.job_id,
                        status=run.status.value,
                        document=document,
                        started_at=run.started_at,
                        finished_at=run.finished_at,
                    )
                )
                await session.execute(statement)

    async def list_runs(self, *, job_id: str | None = None, limit: int = 100) -> list[JobRun]:
        statement = sa.select(job_runs_table.c.document).order_by(
            job_runs_table.c.started_at.desc()
        )
        if job_id:
            statement = statement.where(job_runs_table.c.job_id == job_id)
        async with self.session_factory() as session:
            rows = (await session.execute(statement.limit(limit))).all()
        return [JobRun.from_document(row[0]) for row in rows]

    async def acquire_lock(self, name: str, owner: str, ttl_seconds: int) -> bool:
        now = dt.datetime.now(dt.UTC)
        expires_at = now + dt.timedelta(seconds=ttl_seconds)
        async with self.session_factory() as session:
            try:
                async with session.begin():
                    row = (
                        await session.execute(
                            sa.select(
                                scheduler_locks_table.c.owner,
                                scheduler_locks_table.c.expires_at,
                            )
                            .where(scheduler_locks_table.c.name == name)
                            .with_for_update()
                        )
                    ).first()
                    if row and row[1] > now and row[0] != owner:
                        return False
                    statement = (
                        sa.update(scheduler_locks_table)
                        .where(scheduler_locks_table.c.name == name)
                        .values(owner=owner, expires_at=expires_at)
                        if row
                        else sa.insert(scheduler_locks_table).values(
                            name=name,
                            owner=owner,
                            expires_at=expires_at,
                        )
                    )
                    await session.execute(statement)
            except sa.exc.IntegrityError:
                return False
        return True


class PostgresRemediationRepository(RemediationRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def save_plan(self, plan: RemediationPlan) -> None:
        now = dt.datetime.now(dt.UTC)
        try:
            async with self.session_factory() as session:
                async with session.begin():
                    await session.execute(
                        sa.insert(remediation_plans_table).values(
                            id=plan.id,
                            report_id=plan.report_id,
                            document=plan.to_document(),
                            created_at=now,
                        )
                    )
                    for action in plan.actions:
                        exists = await session.scalar(
                            sa.select(remediation_actions_table.c.id)
                            .where(remediation_actions_table.c.report_id == plan.report_id)
                            .where(remediation_actions_table.c.fingerprint == action.fingerprint)
                        )
                        if exists:
                            continue
                        await session.execute(
                            sa.insert(remediation_actions_table).values(
                                id=action.id,
                                plan_id=plan.id,
                                report_id=plan.report_id,
                                status=action.status.value,
                                fingerprint=action.fingerprint,
                                idempotency_key=action.idempotency_key,
                                document=action.to_document(),
                                created_at=action.created_at,
                                updated_at=now,
                            )
                        )
        except sa.exc.IntegrityError:
            return

    async def claim_execution(self, *, report_id: str, idempotency_key: str) -> bool:
        now = dt.datetime.now(dt.UTC)
        async with self.session_factory() as session:
            try:
                async with session.begin():
                    await session.execute(
                        sa.insert(remediation_executions_table).values(
                            id=new_id("exec"),
                            report_id=report_id,
                            idempotency_key=idempotency_key,
                            status="claimed",
                            created_at=now,
                        )
                    )
            except sa.exc.IntegrityError:
                return False
        return True

    async def get_action(self, action_id: str) -> RemediationAction | None:
        async with self.session_factory() as session:
            row = (
                await session.execute(
                    sa.select(remediation_actions_table.c.document).where(
                        remediation_actions_table.c.id == action_id
                    )
                )
            ).first()
        return _action_from_document(row[0]) if row else None

    async def save_action(self, action: RemediationAction) -> None:
        now = dt.datetime.now(dt.UTC)
        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(
                    sa.update(remediation_actions_table)
                    .where(remediation_actions_table.c.id == action.id)
                    .values(
                        status=action.status.value,
                        idempotency_key=action.idempotency_key,
                        document=action.to_document(),
                        updated_at=now,
                    )
                )

    async def list_actions(
        self, *, report_id: str | None = None, limit: int = 100
    ) -> list[RemediationAction]:
        statement = sa.select(remediation_actions_table.c.document).order_by(
            remediation_actions_table.c.created_at.desc()
        )
        if report_id:
            statement = statement.where(remediation_actions_table.c.report_id == report_id)
        async with self.session_factory() as session:
            rows = (await session.execute(statement.limit(limit))).all()
        return [_action_from_document(row[0]) for row in rows]


def _report_from_document(document: dict[str, Any]) -> DriftReport:
    findings = []
    for item in document.get("findings", []):
        detected_at = item.get("detected_at")
        findings.append(
            DriftFinding(
                id=item["id"],
                baseline_id=item["baseline_id"],
                snapshot_id=item["snapshot_id"],
                resource_key=item["resource_key"],
                resource_type=item["resource_type"],
                drift_type=DriftType(item["drift_type"]),
                path=item["path"],
                expected=item.get("expected"),
                actual=item.get("actual"),
                severity=Severity(item.get("severity", "medium")),
                risk_score=float(item.get("risk_score", 0)),
                status=DriftStatus(item.get("status", "open")),
                policy_violations=item.get("policy_violations", []),
                detected_at=dt.datetime.fromisoformat(detected_at)
                if detected_at
                else dt.datetime.now(dt.UTC),
                fingerprint=item.get("fingerprint", ""),
                trusted=bool(item.get("trusted", True)),
                integrity_notes=item.get("integrity_notes", []),
            )
        )
    summary = document.get("summary", {})
    generated_at = document.get("generated_at")
    return DriftReport(
        id=document["id"],
        baseline_id=document["baseline_id"],
        snapshot_id=document["snapshot_id"],
        findings=findings,
        generated_at=dt.datetime.fromisoformat(generated_at)
        if generated_at
        else dt.datetime.now(dt.UTC),
        policy_results=document.get("policy_results", []),
        risk_score=float(document.get("risk_score", 0)),
        summary=DriftSummary(
            total=int(summary.get("total", len(findings))),
            added=int(summary.get("added", 0)),
            removed=int(summary.get("removed", 0)),
            modified=int(summary.get("modified", 0)),
            by_severity=summary.get("by_severity", {}),
        ),
        scan_completeness=ScanCompleteness(document.get("scan_completeness", "complete")),
        collector_results=document.get("collector_results", []),
        integrity_warnings=document.get("integrity_warnings", []),
    )


def _action_from_document(document: dict[str, Any]) -> RemediationAction:
    created_at = document.get("created_at")
    executed_at = document.get("executed_at")
    approval_expires_at = document.get("approval_expires_at")
    return RemediationAction(
        id=document["id"],
        finding_id=document["finding_id"],
        fingerprint=document["fingerprint"],
        strategy=document["strategy"],
        description=document["description"],
        risk_score=float(document.get("risk_score", 0)),
        command=list(document.get("command", [])),
        runbook_id=document.get("runbook_id"),
        parameters=document.get("parameters", {}),
        status=RemediationStatus(document.get("status", "planned")),
        requires_approval=bool(document.get("requires_approval", True)),
        approved_by=document.get("approved_by"),
        approval_expires_at=dt.datetime.fromisoformat(approval_expires_at)
        if approval_expires_at
        else None,
        idempotency_key=document.get("idempotency_key"),
        dry_run=bool(document.get("dry_run", True)),
        output=document.get("output", ""),
        error=document.get("error", ""),
        executor_mode=document.get("executor_mode", "unknown"),
        simulated=bool(document.get("simulated", False)),
        created_at=dt.datetime.fromisoformat(created_at)
        if created_at
        else dt.datetime.now(dt.UTC),
        executed_at=dt.datetime.fromisoformat(executed_at) if executed_at else None,
    )


def _policy_from_document(document: dict[str, Any]) -> PolicyRule:
    created_at = document.get("created_at")
    updated_at = document.get("updated_at")
    return PolicyRule(
        id=document["id"],
        name=document["name"],
        description=document.get("description", ""),
        conditions=[
            PolicyCondition(
                field=item["field"],
                operator=RuleOperator(item["operator"]),
                value=item.get("value"),
            )
            for item in document.get("conditions", [])
        ],
        effect=PolicyEffect(document.get("effect", "warn")),
        severity=Severity(document.get("severity", "medium")),
        risk_delta=float(document.get("risk_delta", 0)),
        enabled=bool(document.get("enabled", True)),
        tags=document.get("tags", {}),
        created_at=dt.datetime.fromisoformat(created_at)
        if created_at
        else dt.datetime.now(dt.UTC),
        updated_at=dt.datetime.fromisoformat(updated_at)
        if updated_at
        else dt.datetime.now(dt.UTC),
    )
