from __future__ import annotations

from drift_engine.core.baseline import BaselineManager
from drift_engine.core.drift_detector import DriftDetector
from drift_engine.core.models import StateSnapshot
from drift_engine.policies.engine import PolicyEngine


def test_default_policy_flags_encryption_disabled() -> None:
    resources = {
        "aws::_::us-east-1::volume::vol-1": {
            "resource_type": "volume",
            "encryption": True,
        }
    }
    actual = {
        "aws::_::us-east-1::volume::vol-1": {
            "resource_type": "volume",
            "encryption": False,
        }
    }
    baseline = BaselineManager().create(name="prod", resources=resources)
    report = DriftDetector().detect(baseline, StateSnapshot(source="test", resources=actual))

    result = PolicyEngine.default().evaluate_report(report)
    PolicyEngine.default().apply_risk(report, result)

    assert not result.passed
    assert result.violations[0].rule_name == "Encryption disabled"
    assert report.risk_score > 50


def test_kubernetes_policy_flags_public_load_balancer() -> None:
    unchanged = {
        "kubernetes::_::_::kubernetes::prod/deployments/checkout": {
            "resource_type": "kubernetes",
            "kind": "deployments",
            "namespace": "prod",
            "name": "checkout",
            "spec": {"replicas": 2},
        }
    }
    actual = {
        **unchanged,
        "kubernetes::_::_::kubernetes::prod/services/checkout": {
            "resource_type": "kubernetes",
            "kind": "services",
            "namespace": "prod",
            "name": "checkout",
            "spec": {"type": "LoadBalancer"},
        }
    }
    baseline = BaselineManager().create(name="prod", resources=unchanged)
    report = DriftDetector().detect(baseline, StateSnapshot(source="test", resources=actual))

    result = PolicyEngine.default().evaluate_report(report)
    PolicyEngine.default().apply_risk(report, result)

    assert result.violations[0].rule_name == "Kubernetes public service exposure"
    assert report.risk_score >= 90


def test_kubernetes_policy_flags_replica_drift() -> None:
    resources = {
        "kubernetes::_::_::kubernetes::prod/deployments/checkout": {
            "resource_type": "kubernetes",
            "kind": "deployments",
            "spec": {"replicas": 2},
        }
    }
    actual = {
        "kubernetes::_::_::kubernetes::prod/deployments/checkout": {
            "resource_type": "kubernetes",
            "kind": "deployments",
            "spec": {"replicas": 4},
        }
    }
    baseline = BaselineManager().create(name="prod", resources=resources)
    report = DriftDetector().detect(baseline, StateSnapshot(source="test", resources=actual))

    result = PolicyEngine.default().evaluate_report(report)

    assert result.violations[0].rule_name == "Kubernetes replica drift"
