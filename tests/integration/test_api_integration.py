from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from drift_engine.core.models import Baseline


def test_health_and_baseline_create(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from config.settings import get_settings
    from drift_engine.api.app import create_app
    from drift_engine.api.dependencies import get_engine, get_metrics

    monkeypatch.setenv("DRIFT_ENVIRONMENT", "local")
    monkeypatch.setenv("DRIFT_AUTH_REQUIRED", "false")
    monkeypatch.setenv("DRIFT_REMEDIATION_ENABLED", "true")
    monkeypatch.setenv("DRIFT_REMEDIATION_DRY_RUN", "true")
    monkeypatch.setenv("DRIFT_ALLOW_DEV_AUTH", "true")
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_metrics.cache_clear()

    async def fake_kubernetes_check(
        self: object,
        namespaces: list[str] | None = None,
    ) -> dict[str, object]:
        del self
        return {
            "integration": "kubernetes",
            "ready": True,
            "context": "kind-platform",
            "namespaces": namespaces or [],
            "checks": [{"name": "kubectl", "status": "passed", "details": {}, "error": None}],
        }

    monkeypatch.setattr(
        "drift_engine.integrations.kubernetes.KubernetesIntegrationChecker.check",
        fake_kubernetes_check,
    )

    client = TestClient(create_app())

    health = client.get("/health/live")
    assert health.status_code == 200

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert "System Drift Engine" in dashboard.text
    assert "Integrations" in dashboard.text
    assert "Report history" in dashboard.text
    assert "Remediation queue" in dashboard.text
    assert "Audit trail" in dashboard.text
    assert "Create job" in dashboard.text
    assert "Approve action" in dashboard.text
    assert "Execute approved" in dashboard.text or "Simulate execution" in dashboard.text
    assert 'href="/favicon.ico"' in dashboard.text

    favicon = client.get("/favicon.ico")
    assert favicon.status_code == 200
    assert favicon.headers["content-type"].startswith("image/svg+xml")
    assert "<svg" in favicon.text

    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "/favicon.ico" in docs.text

    integrations = client.get("/integrations")
    assert integrations.status_code == 200
    integration_names = {item["name"] for item in integrations.json()}
    assert {"kubernetes", "aws", "azure"}.issubset(integration_names)

    kubernetes_check = client.get("/integrations/kubernetes/check?namespaces=drift-demo")
    assert kubernetes_check.status_code == 200
    assert kubernetes_check.json()["namespaces"] == ["drift-demo"]

    response = client.post(
        "/baselines",
        json={
            "name": "prod",
            "resources": {
                "local::_::_::package::openssl": {
                    "resource_type": "package",
                    "name": "openssl",
                    "version": "3.0.0",
                }
            },
        },
    )

    assert response.status_code == 201
    baseline = response.json()
    assert baseline["name"] == "prod"

    job = client.post(
        "/jobs",
        json={
            "name": "prod-hourly",
            "baseline_id": baseline["id"],
            "interval_seconds": 3600,
            "collector_names": ["file"],
        },
    )
    assert job.status_code == 201
    assert job.json()["baseline_id"] == baseline["id"]

    audit = client.get("/audit")
    assert audit.status_code == 200
    actions = {event["action"] for event in audit.json()}
    assert "baseline.created" in actions
    assert "job.created" in actions

    missing_path = "tests/.tmp/definitely-missing-remediation-target"
    drift_baseline = client.post(
        "/baselines",
        json={
            "name": "remediation-target",
            "resources": {
                f"local::_::_::file::{missing_path}": {
                    "resource_type": "file",
                    "path": missing_path,
                    "exists": True,
                    "sha256": "expected-hash",
                }
            },
        },
    )
    assert drift_baseline.status_code == 201

    drift_report = client.post(
        "/drifts/run",
        json={
            "baseline_id": drift_baseline.json()["id"],
            "collector_names": ["file"],
            "scope": {"file_paths": [missing_path]},
        },
    )
    assert drift_report.status_code == 200
    assert drift_report.json()["summary"]["total"] >= 1

    plan = client.post(f"/remediation/reports/{drift_report.json()['id']}/plan")
    assert plan.status_code == 200
    plan_actions = plan.json()["actions"]
    assert len(plan_actions) >= 1

    for action in plan_actions:
        approval = client.post(f"/remediation/actions/{action['id']}/approve", json={})
        assert approval.status_code == 200

    execution = client.post(
        f"/remediation/reports/{drift_report.json()['id']}/execute",
        headers={"Idempotency-Key": "test-remediation-execution"},
    )
    assert execution.status_code == 200
    assert {action["status"] for action in execution.json()} == {"skipped"}


def test_dashboard_asset_route_recovers_stale_hashed_asset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from drift_engine.api.app import create_app
    from drift_engine.api.routes import ui

    dashboard_dir = Path("tests/.tmp") / f"dashboard-{uuid4().hex}"
    assets_dir = dashboard_dir / "assets"
    assets_dir.mkdir(parents=True)

    (assets_dir / "index-livehash.js").write_text("console.log('live build');", encoding="utf-8")
    (dashboard_dir / "index.html").write_text(
        (
            "<!doctype html><html><head>"
            '<script type="module" src="/assets/index-stalehash.js"></script>'
            "</head><body><div id=\"root\"></div></body></html>"
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(ui, "DASHBOARD_DIR", dashboard_dir)
    monkeypatch.setattr(ui, "DASHBOARD_INDEX", dashboard_dir / "index.html")

    client = TestClient(create_app())

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert "/assets/index-stalehash.js" in dashboard.text

    asset = client.get("/assets/index-stalehash.js")
    assert asset.status_code == 200
    assert "console.log('live build');" in asset.text


def test_staging_refuses_startup_without_auth_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DRIFT_ENVIRONMENT", "staging")
    monkeypatch.setenv("DRIFT_AUTH_REQUIRED", "true")
    monkeypatch.setenv("DRIFT_API_KEYS", "")
    monkeypatch.setenv("DRIFT_SERVICE_ACCOUNTS", "")
    monkeypatch.setenv("DRIFT_ALLOW_DEV_AUTH", "false")

    from config.settings import get_settings

    get_settings.cache_clear()

    with pytest.raises(ValueError, match="required in staging and production"):
        get_settings().validate_runtime_security()


def test_drift_scan_repairs_legacy_unsigned_baseline_in_local_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("fastapi")

    from config.settings import get_settings
    from drift_engine.api.app import create_app
    from drift_engine.api.dependencies import get_engine, get_metrics

    monkeypatch.setenv("DRIFT_ENVIRONMENT", "local")
    monkeypatch.setenv("DRIFT_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("DRIFT_BASELINE_SIGNING_SECRET", "local-test-secret")
    monkeypatch.setenv("DRIFT_AUTH_REQUIRED", "false")
    monkeypatch.setenv("DRIFT_ALLOW_DEV_AUTH", "true")
    monkeypatch.setenv("DRIFT_METRICS_ENABLED", "false")
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_metrics.cache_clear()

    tracked_dir = Path("tests/.tmp") / f"legacy-baseline-{uuid4().hex}"
    tracked_dir.mkdir(parents=True, exist_ok=True)
    tracked_file = tracked_dir / "openssl.txt"
    tracked_file.write_text("openssl=3.0.0", encoding="utf-8")
    digest = hashlib.sha256(tracked_file.read_bytes()).hexdigest()

    client = TestClient(create_app())
    with client:
        app = cast(FastAPI, client.app)
        engine = app.state.drift_engine
        baseline = Baseline(
            name="legacy-prod",
            resources={
                f"local::_::_::file::{tracked_file}": {
                    "resource_type": "file",
                    "path": str(tracked_file),
                    "exists": True,
                    "is_file": True,
                    "sha256": digest,
                }
            },
        )
        asyncio.run(engine.baselines.save(baseline))

        response = client.post(
            "/drifts/run",
            json={
                "baseline_id": baseline.id,
                "collector_names": ["file"],
                "scope": {"file_paths": [str(tracked_file)]},
            },
        )

        assert response.status_code == 200

        repaired = asyncio.run(engine.baselines.get(baseline.id))
        assert repaired is not None
        assert repaired.signature
