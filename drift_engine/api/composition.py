from __future__ import annotations

from config.settings import Settings
from drift_engine.core.baseline import BaselineManager
from drift_engine.events.bus import EventBus
from drift_engine.events.handlers import log_event
from drift_engine.policies.engine import PolicyEngine
from drift_engine.policies.models import PolicyRule
from drift_engine.policies.rules import default_policy_rules
from drift_engine.remediation.approval import ApprovalPolicy
from drift_engine.remediation.engine import RemediationEngine


def build_event_bus() -> EventBus:
    events = EventBus()
    events.subscribe(None, log_event)
    return events


def build_baseline_manager(settings: Settings) -> BaselineManager:
    secret = (
        settings.baseline_signing_secret.get_secret_value()
        if settings.baseline_signing_secret
        else None
    )
    return BaselineManager(
        signing_secret=secret,
        allow_legacy_unsigned_repair=settings.environment in {"local", "test"},
    )


def build_policy_engine(persisted_policies: list[PolicyRule]) -> PolicyEngine:
    return PolicyEngine([*default_policy_rules(), *persisted_policies])


def build_remediation_engine(settings: Settings) -> RemediationEngine:
    return RemediationEngine(
        approval=ApprovalPolicy(
            auto_approve_below_risk=settings.remediation_auto_approve_below_risk,
        ),
        enabled=settings.remediation_enabled,
        dry_run=settings.remediation_dry_run,
    )
