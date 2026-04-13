from __future__ import annotations

from drift_engine.core.models import Severity
from drift_engine.policies.models import PolicyCondition, PolicyEffect, PolicyRule, RuleOperator


def default_policy_rules() -> list[PolicyRule]:
    return [
        PolicyRule(
            name="Public network exposure",
            description="Public ingress or firewall exposure materially increases blast radius.",
            conditions=[
                PolicyCondition("resource_type", RuleOperator.IN, ["security_group", "network"]),
                PolicyCondition("actual", RuleOperator.CONTAINS, "0.0.0.0/0"),
            ],
            effect=PolicyEffect.REQUIRE_APPROVAL,
            severity=Severity.CRITICAL,
            risk_delta=25.0,
            tags={"control": "network-boundary"},
        ),
        PolicyRule(
            name="Privileged workload enabled",
            description="Privileged workloads require explicit review.",
            conditions=[
                PolicyCondition("path", RuleOperator.MATCHES, "*.privileged*"),
                PolicyCondition("actual", RuleOperator.EQUALS, True),
            ],
            effect=PolicyEffect.BLOCK,
            severity=Severity.CRITICAL,
            risk_delta=30.0,
            tags={"control": "least-privilege"},
        ),
        PolicyRule(
            name="Encryption disabled",
            description="Encryption drift must be treated as high-risk.",
            conditions=[
                PolicyCondition("path", RuleOperator.MATCHES, "*.encryption*"),
                PolicyCondition("actual", RuleOperator.IN, [False, "disabled", "off", None]),
            ],
            effect=PolicyEffect.BLOCK,
            severity=Severity.CRITICAL,
            risk_delta=35.0,
            tags={"control": "data-protection"},
        ),
        PolicyRule(
            name="Service stopped or disabled",
            description="Core service availability drift should be reviewed.",
            conditions=[
                PolicyCondition("resource_type", RuleOperator.EQUALS, "service"),
                PolicyCondition("actual", RuleOperator.CONTAINS, "inactive"),
            ],
            effect=PolicyEffect.WARN,
            severity=Severity.HIGH,
            risk_delta=10.0,
            tags={"control": "availability"},
        ),
        PolicyRule(
            name="Unexpected administrative user",
            description="Added users or users with administrative group membership are high risk.",
            conditions=[
                PolicyCondition("resource_type", RuleOperator.EQUALS, "user"),
                PolicyCondition("actual", RuleOperator.CONTAINS, "admin"),
            ],
            effect=PolicyEffect.REQUIRE_APPROVAL,
            severity=Severity.HIGH,
            risk_delta=20.0,
            tags={"control": "identity"},
        ),
        PolicyRule(
            name="Kubernetes public service exposure",
            description="LoadBalancer or NodePort exposure changes require platform review.",
            conditions=[
                PolicyCondition("resource_type", RuleOperator.EQUALS, "kubernetes"),
                PolicyCondition("actual", RuleOperator.CONTAINS, "LoadBalancer"),
            ],
            effect=PolicyEffect.REQUIRE_APPROVAL,
            severity=Severity.CRITICAL,
            risk_delta=25.0,
            tags={"control": "kubernetes-network-boundary"},
        ),
        PolicyRule(
            name="Kubernetes workload container spec changed",
            description=(
                "Container image or security context drift changes workload supply-chain risk."
            ),
            conditions=[
                PolicyCondition("resource_type", RuleOperator.EQUALS, "kubernetes"),
                PolicyCondition("path", RuleOperator.MATCHES, "*.containers"),
            ],
            effect=PolicyEffect.REQUIRE_APPROVAL,
            severity=Severity.HIGH,
            risk_delta=18.0,
            tags={"control": "kubernetes-workload-integrity"},
        ),
        PolicyRule(
            name="Kubernetes replica drift",
            description="Replica count changes can affect availability and capacity assumptions.",
            conditions=[
                PolicyCondition("resource_type", RuleOperator.EQUALS, "kubernetes"),
                PolicyCondition("path", RuleOperator.MATCHES, "*.replicas"),
            ],
            effect=PolicyEffect.WARN,
            severity=Severity.HIGH,
            risk_delta=8.0,
            tags={"control": "kubernetes-availability"},
        ),
        PolicyRule(
            name="Kubernetes RBAC changed",
            description="RBAC role or binding drift changes cluster authorization boundaries.",
            conditions=[
                PolicyCondition("resource_type", RuleOperator.EQUALS, "kubernetes"),
                PolicyCondition("actual", RuleOperator.CONTAINS, "rbac.authorization.k8s.io"),
            ],
            effect=PolicyEffect.REQUIRE_APPROVAL,
            severity=Severity.CRITICAL,
            risk_delta=28.0,
            tags={"control": "kubernetes-authorization"},
        ),
    ]
