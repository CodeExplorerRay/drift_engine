from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from config.settings import Settings
from drift_engine.api.dependencies import build_runtime_engine
from drift_engine.core.models import StateSnapshot
from drift_engine.policies.models import PolicyCondition, PolicyRule, RuleOperator


async def test_runtime_engine_persists_baselines_snapshots_and_reports() -> None:
    pytest.importorskip("aiosqlite")

    database_dir = Path("tests/.tmp")
    database_dir.mkdir(exist_ok=True)
    database_path = database_dir / f"{uuid4().hex}.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"
    settings = Settings(
        storage_backend="postgres",
        database_url=database_url,
        auto_create_schema=True,
        metrics_enabled=False,
    )
    engine, database = await build_runtime_engine(settings)
    assert database is not None

    baseline = engine.baseline_manager.create(
        name="durable-prod",
        resources={
            "local::_::_::package::openssl": {
                "resource_type": "package",
                "name": "openssl",
                "version": "3.0.0",
            }
        },
    )
    snapshot = StateSnapshot(
        source="test",
        resources={
            "local::_::_::package::openssl": {
                "resource_type": "package",
                "name": "openssl",
                "version": "3.0.1",
            }
        },
    )
    report = engine.detector.detect(baseline, snapshot)
    policy = PolicyRule(
        name="Durable custom policy",
        conditions=[PolicyCondition("resource_type", RuleOperator.EQUALS, "package")],
    )

    await engine.baselines.save(baseline)
    await engine.snapshots.save(snapshot)
    await engine.reports.save(report)
    assert engine.policy_repository is not None
    await engine.policy_repository.save(policy)
    await database.dispose()

    reloaded_engine, reloaded_database = await build_runtime_engine(settings)
    assert reloaded_database is not None
    try:
        assert await reloaded_engine.baselines.get(baseline.id) is not None
        assert await reloaded_engine.snapshots.get(snapshot.id) is not None
        assert await reloaded_engine.reports.get(report.id) is not None
        assert any(rule.id == policy.id for rule in reloaded_engine.policies.rules)
    finally:
        await reloaded_database.dispose()
        database_path.unlink(missing_ok=True)
        database_path.with_suffix(".db-shm").unlink(missing_ok=True)
        database_path.with_suffix(".db-wal").unlink(missing_ok=True)
