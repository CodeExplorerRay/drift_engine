from __future__ import annotations

import pytest

from drift_engine.collectors.base import StaticCollector
from drift_engine.collectors.registry import CollectorRegistry
from drift_engine.core.baseline import BaselineManager
from drift_engine.core.engine import DriftEngine
from drift_engine.storage.base import (
    InMemoryBaselineRepository,
    InMemoryDriftReportRepository,
    InMemorySnapshotRepository,
)
from drift_engine.telemetry.metrics import MetricsRecorder


@pytest.fixture()
def baseline_manager() -> BaselineManager:
    return BaselineManager(signing_secret="test-secret")  # noqa: S106


@pytest.fixture()
def expected_resources() -> dict[str, dict[str, object]]:
    return {
        "local::_::_::package::openssl": {
            "resource_type": "package",
            "name": "openssl",
            "version": "3.0.0",
        },
        "local::_::_::service::sshd": {
            "resource_type": "service",
            "name": "sshd",
            "active": "active",
        },
    }


@pytest.fixture()
def actual_resources() -> dict[str, dict[str, object]]:
    return {
        "local::_::_::package::openssl": {
            "resource_type": "package",
            "name": "openssl",
            "version": "3.0.1",
        },
        "local::_::_::service::sshd": {
            "resource_type": "service",
            "name": "sshd",
            "active": "inactive",
        },
    }


@pytest.fixture()
def engine(
    actual_resources: dict[str, dict[str, object]], baseline_manager: BaselineManager
) -> DriftEngine:
    registry = CollectorRegistry([StaticCollector("static", actual_resources)])
    return DriftEngine(
        collectors=registry,
        baselines=InMemoryBaselineRepository(),
        snapshots=InMemorySnapshotRepository(),
        reports=InMemoryDriftReportRepository(),
        baseline_manager=baseline_manager,
        metrics=MetricsRecorder(enabled=False),
    )
