from __future__ import annotations

import pytest


def test_health_and_baseline_create(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from drift_engine.api.app import create_app

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
    assert "Execute approved" in dashboard.text

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
