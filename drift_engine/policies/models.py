from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from drift_engine.core.models import Severity, new_id, utcnow


class PolicyEffect(StrEnum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    SUPPRESS = "suppress"
    REQUIRE_APPROVAL = "require_approval"


class RuleOperator(StrEnum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    IN = "in"
    MATCHES = "matches"
    EXISTS = "exists"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"


@dataclass(slots=True)
class PolicyCondition:
    field: str
    operator: RuleOperator
    value: Any = None


@dataclass(slots=True)
class PolicyRule:
    name: str
    conditions: list[PolicyCondition]
    effect: PolicyEffect = PolicyEffect.WARN
    severity: Severity = Severity.MEDIUM
    risk_delta: float = 0.0
    id: str = field(default_factory=lambda: new_id("policy"))
    description: str = ""
    enabled: bool = True
    tags: dict[str, str] = field(default_factory=dict)
    created_at: dt.datetime = field(default_factory=utcnow)
    updated_at: dt.datetime = field(default_factory=utcnow)

    def to_document(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "conditions": [
                {"field": item.field, "operator": item.operator.value, "value": item.value}
                for item in self.conditions
            ],
            "effect": self.effect.value,
            "severity": self.severity.value,
            "risk_delta": self.risk_delta,
            "enabled": self.enabled,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(slots=True)
class PolicyViolation:
    rule_id: str
    rule_name: str
    finding_id: str
    fingerprint: str
    effect: PolicyEffect
    severity: Severity
    risk_delta: float
    message: str

    def to_document(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "finding_id": self.finding_id,
            "fingerprint": self.fingerprint,
            "effect": self.effect.value,
            "severity": self.severity.value,
            "risk_delta": self.risk_delta,
            "message": self.message,
        }


@dataclass(slots=True)
class PolicyEvaluationResult:
    violations: list[PolicyViolation] = field(default_factory=list)
    evaluated_rules: int = 0

    @property
    def passed(self) -> bool:
        return not any(v.effect == PolicyEffect.BLOCK for v in self.violations)

    @property
    def total_risk_delta(self) -> float:
        return sum(v.risk_delta for v in self.violations)

    def to_document(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "evaluated_rules": self.evaluated_rules,
            "total_risk_delta": self.total_risk_delta,
            "violations": [violation.to_document() for violation in self.violations],
        }
