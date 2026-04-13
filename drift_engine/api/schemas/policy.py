from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from drift_engine.core.models import Severity
from drift_engine.policies.models import PolicyCondition, PolicyEffect, PolicyRule, RuleOperator


class PolicyConditionSchema(BaseModel):
    field: str
    operator: RuleOperator
    value: Any = None


class PolicyRuleCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    conditions: list[PolicyConditionSchema]
    effect: PolicyEffect = PolicyEffect.WARN
    severity: Severity = Severity.MEDIUM
    risk_delta: float = 0.0
    enabled: bool = True
    tags: dict[str, str] = Field(default_factory=dict)

    def to_domain(self) -> PolicyRule:
        return PolicyRule(
            name=self.name,
            description=self.description,
            conditions=[
                PolicyCondition(field=item.field, operator=item.operator, value=item.value)
                for item in self.conditions
            ],
            effect=self.effect,
            severity=self.severity,
            risk_delta=self.risk_delta,
            enabled=self.enabled,
            tags=self.tags,
        )


class PolicyRuleResponse(BaseModel):
    id: str
    name: str
    description: str
    conditions: list[dict[str, Any]]
    effect: str
    severity: str
    risk_delta: float
    enabled: bool
    tags: dict[str, str]
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(cls, rule: PolicyRule) -> PolicyRuleResponse:
        return cls(**rule.to_document())
