from __future__ import annotations

from collections.abc import Iterable

from drift_engine.core.models import SEVERITY_BASE_RISK, Baseline, DriftReport, StateSnapshot
from drift_engine.policies.evaluator import PolicyEvaluator
from drift_engine.policies.models import PolicyEvaluationResult, PolicyRule
from drift_engine.policies.rules import default_enterprise_rules


class PolicyEngine:
    def __init__(
        self,
        rules: Iterable[PolicyRule] | None = None,
        evaluator: PolicyEvaluator | None = None,
    ) -> None:
        self.rules = list(rules or [])
        self.evaluator = evaluator or PolicyEvaluator()

    @classmethod
    def default(cls) -> PolicyEngine:
        return cls(default_enterprise_rules())

    def add_rule(self, rule: PolicyRule) -> None:
        self.rules.append(rule)

    def evaluate_report(
        self,
        report: DriftReport,
        *,
        snapshot: StateSnapshot | None = None,
        baseline: Baseline | None = None,
    ) -> PolicyEvaluationResult:
        del snapshot, baseline
        result = PolicyEvaluationResult(
            evaluated_rules=len([rule for rule in self.rules if rule.enabled])
        )
        for finding in report.findings:
            for rule in self.rules:
                violation = self.evaluator.evaluate(rule, finding)
                if violation is not None:
                    finding.policy_violations.append(violation.rule_id)
                    if (
                        SEVERITY_BASE_RISK[violation.severity]
                        > SEVERITY_BASE_RISK[finding.severity]
                    ):
                        finding.severity = violation.severity
                    result.violations.append(violation)
        return result

    def apply_risk(self, report: DriftReport, result: PolicyEvaluationResult) -> None:
        deltas_by_finding: dict[str, float] = {}
        for violation in result.violations:
            deltas_by_finding[violation.finding_id] = (
                deltas_by_finding.get(violation.finding_id, 0.0) + violation.risk_delta
            )

        for finding in report.findings:
            base_risk = SEVERITY_BASE_RISK[finding.severity]
            finding.risk_score = round(
                min(
                    100.0,
                    max(finding.risk_score, base_risk)
                    + deltas_by_finding.get(finding.id, 0),
                ),
                2,
            )

        if report.findings:
            report.risk_score = report.aggregate_risk(report.findings)
            report.summary = report.build_summary(report.findings)
