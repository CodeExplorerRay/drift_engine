from __future__ import annotations

import fnmatch
from typing import Any

from drift_engine.core.models import DriftFinding
from drift_engine.policies.models import PolicyCondition, PolicyRule, PolicyViolation, RuleOperator
from drift_engine.utils.serialization import canonical_dumps, deep_get


class PolicyEvaluator:
    def evaluate(self, rule: PolicyRule, finding: DriftFinding) -> PolicyViolation | None:
        if not rule.enabled:
            return None
        document = finding.to_document()
        if not all(self._matches(condition, document) for condition in rule.conditions):
            return None
        return PolicyViolation(
            rule_id=rule.id,
            rule_name=rule.name,
            finding_id=finding.id,
            fingerprint=finding.fingerprint,
            effect=rule.effect,
            severity=rule.severity,
            risk_delta=rule.risk_delta,
            message=rule.description or f"{rule.name} matched {finding.resource_key}",
        )

    def _matches(self, condition: PolicyCondition, document: dict[str, Any]) -> bool:
        actual = self._value_for(condition.field, document)
        expected = condition.value

        if condition.operator == RuleOperator.EXISTS:
            return actual is not None
        if condition.operator == RuleOperator.EQUALS:
            return bool(actual == expected)
        if condition.operator == RuleOperator.NOT_EQUALS:
            return bool(actual != expected)
        if condition.operator == RuleOperator.IN:
            return bool(actual in expected) if isinstance(expected, list | tuple | set) else False
        if condition.operator == RuleOperator.CONTAINS:
            if isinstance(actual, list | tuple | set):
                return bool(expected in actual)
            if isinstance(actual, dict):
                return str(expected).lower() in canonical_dumps(actual).lower()
            return str(expected).lower() in str(actual).lower()
        if condition.operator == RuleOperator.MATCHES:
            return fnmatch.fnmatch(str(actual), str(expected))
        if condition.operator == RuleOperator.GREATER_THAN:
            return float(actual) > float(expected)
        if condition.operator == RuleOperator.LESS_THAN:
            return float(actual) < float(expected)

    @staticmethod
    def _value_for(path: str, document: dict[str, Any]) -> Any:
        if path in document:
            return document[path]
        return deep_get(document, path)
