from __future__ import annotations

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.requests import Request

from config.settings import Settings, get_settings
from drift_engine.collectors.registry import CollectorRegistry
from drift_engine.core.baseline import BaselineManager
from drift_engine.core.engine import DriftEngine
from drift_engine.events.bus import EventBus
from drift_engine.events.handlers import log_event
from drift_engine.policies.engine import PolicyEngine
from drift_engine.policies.models import PolicyRule
from drift_engine.policies.rules import default_policy_rules
from drift_engine.remediation.approval import ApprovalPolicy
from drift_engine.remediation.engine import RemediationEngine
from drift_engine.storage.base import (
    AuditRepository,
    BaselineRepository,
    DriftReportRepository,
    InMemoryAuditRepository,
    InMemoryBaselineRepository,
    InMemoryDriftReportRepository,
    InMemoryJobRepository,
    InMemoryPolicyRepository,
    InMemoryRemediationRepository,
    InMemorySnapshotRepository,
    JobRepository,
    PolicyRepository,
    RemediationRepository,
    SnapshotRepository,
)
from drift_engine.storage.postgres import (
    PostgresAuditRepository,
    PostgresBaselineRepository,
    PostgresDriftReportRepository,
    PostgresJobRepository,
    PostgresPolicyRepository,
    PostgresRemediationRepository,
    PostgresSnapshotRepository,
    build_session_factory,
    create_schema,
)
from drift_engine.storage.postgres import (
    build_engine as build_postgres_engine,
)
from drift_engine.telemetry.metrics import MetricsRecorder


@lru_cache(maxsize=1)
def get_metrics() -> MetricsRecorder:
    return MetricsRecorder(enabled=get_settings().metrics_enabled)


@lru_cache(maxsize=1)
def get_engine() -> DriftEngine:
    return build_engine_from_repositories(
        settings=get_settings(),
        baselines=InMemoryBaselineRepository(),
        snapshots=InMemorySnapshotRepository(),
        reports=InMemoryDriftReportRepository(),
        policy_repository=InMemoryPolicyRepository(),
        audit_repository=InMemoryAuditRepository(),
        job_repository=InMemoryJobRepository(),
        remediation_repository=InMemoryRemediationRepository(),
        persisted_policies=[],
    )


def request_engine(request: Request) -> DriftEngine:
    engine = getattr(request.app.state, "drift_engine", None)
    if isinstance(engine, DriftEngine):
        return engine
    return get_engine()


async def build_runtime_engine(settings: Settings) -> tuple[DriftEngine, AsyncEngine | None]:
    if settings.resolved_storage_backend != "postgres":
        return get_engine(), None

    database = build_postgres_engine(settings.database_url)
    if settings.auto_create_schema:
        await create_schema(database)
    session_factory = build_session_factory(database)
    policy_repository = PostgresPolicyRepository(session_factory)
    audit_repository = PostgresAuditRepository(session_factory)
    job_repository = PostgresJobRepository(session_factory)
    remediation_repository = PostgresRemediationRepository(session_factory)
    persisted_policies = await policy_repository.list()
    engine = build_engine_from_repositories(
        settings=settings,
        baselines=PostgresBaselineRepository(session_factory),
        snapshots=PostgresSnapshotRepository(session_factory),
        reports=PostgresDriftReportRepository(session_factory),
        policy_repository=policy_repository,
        audit_repository=audit_repository,
        job_repository=job_repository,
        remediation_repository=remediation_repository,
        persisted_policies=persisted_policies,
    )
    return engine, database


def build_engine_from_repositories(
    *,
    settings: Settings,
    baselines: BaselineRepository,
    snapshots: SnapshotRepository,
    reports: DriftReportRepository,
    policy_repository: PolicyRepository | None,
    audit_repository: AuditRepository | None,
    job_repository: JobRepository | None,
    remediation_repository: RemediationRepository | None,
    persisted_policies: list[PolicyRule],
) -> DriftEngine:
    events = EventBus()
    events.subscribe(None, log_event)
    secret = (
        settings.baseline_signing_secret.get_secret_value()
        if settings.baseline_signing_secret
        else None
    )
    policies = PolicyEngine([*default_policy_rules(), *persisted_policies])
    return DriftEngine(
        collectors=CollectorRegistry.default(settings),
        baselines=baselines,
        snapshots=snapshots,
        reports=reports,
        baseline_manager=BaselineManager(
            signing_secret=secret,
            allow_legacy_unsigned_repair=settings.environment in {"local", "test"},
        ),
        policies=policies,
        policy_repository=policy_repository,
        audit_repository=audit_repository,
        job_repository=job_repository,
        remediation_repository=remediation_repository,
        remediation=RemediationEngine(
            approval=ApprovalPolicy(
                auto_approve_below_risk=settings.remediation_auto_approve_below_risk,
            ),
            enabled=settings.remediation_enabled,
            dry_run=settings.remediation_dry_run,
        ),
        events=events,
        metrics=get_metrics(),
    )


def settings_dependency() -> Settings:
    return get_settings()
