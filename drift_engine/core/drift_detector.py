from __future__ import annotations

import fnmatch
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from drift_engine.core.models import (
    Baseline,
    DriftFinding,
    DriftReport,
    DriftType,
    Severity,
    StateSnapshot,
)


@dataclass(slots=True)
class DriftDetectorConfig:
    ignored_paths: set[str] = field(default_factory=set)
    critical_paths: set[str] = field(
        default_factory=lambda: {
            "*.security_group*",
            "*.firewall*",
            "*.iam*",
            "*.policy*",
            "*.public_access*",
            "*.encryption*",
            "*.privileged*",
        }
    )
    high_paths: set[str] = field(
        default_factory=lambda: {
            "*.version",
            "*.enabled",
            "*.status",
            "*.mode",
            "*.owner",
            "*.permissions",
        }
    )


class DriftDetector:
    """Computes deterministic drift findings between a baseline and current state."""

    def __init__(self, config: DriftDetectorConfig | None = None) -> None:
        self.config = config or DriftDetectorConfig()

    def detect(self, baseline: Baseline, snapshot: StateSnapshot) -> DriftReport:
        findings: list[DriftFinding] = []
        expected_resources = baseline.resources
        actual_resources = snapshot.resources

        for resource_key in sorted(expected_resources.keys() - actual_resources.keys()):
            findings.append(
                self._finding(
                    baseline=baseline,
                    snapshot=snapshot,
                    resource_key=resource_key,
                    drift_type=DriftType.REMOVED,
                    path="$",
                    expected=expected_resources[resource_key],
                    actual=None,
                )
            )

        for resource_key in sorted(actual_resources.keys() - expected_resources.keys()):
            findings.append(
                self._finding(
                    baseline=baseline,
                    snapshot=snapshot,
                    resource_key=resource_key,
                    drift_type=DriftType.ADDED,
                    path="$",
                    expected=None,
                    actual=actual_resources[resource_key],
                )
            )

        for resource_key in sorted(expected_resources.keys() & actual_resources.keys()):
            expected = expected_resources[resource_key]
            actual = actual_resources[resource_key]
            for path, expected_value, actual_value in self._diff(expected, actual):
                if self._is_ignored(path):
                    continue
                findings.append(
                    self._finding(
                        baseline=baseline,
                        snapshot=snapshot,
                        resource_key=resource_key,
                        drift_type=DriftType.MODIFIED,
                        path=path,
                        expected=expected_value,
                        actual=actual_value,
                    )
                )

        return DriftReport(baseline_id=baseline.id, snapshot_id=snapshot.id, findings=findings)

    def _diff(self, expected: Any, actual: Any, path: str = "$") -> Iterable[tuple[str, Any, Any]]:
        if isinstance(expected, dict) and isinstance(actual, dict):
            keys = sorted(expected.keys() | actual.keys())
            for key in keys:
                child_path = f"{path}.{key}"
                if key not in expected:
                    yield child_path, None, actual[key]
                elif key not in actual:
                    yield child_path, expected[key], None
                else:
                    yield from self._diff(expected[key], actual[key], child_path)
            return

        if isinstance(expected, list) and isinstance(actual, list):
            if self._stable_list(expected) and self._stable_list(actual):
                if sorted(expected) != sorted(actual):
                    yield path, expected, actual
            elif expected != actual:
                yield path, expected, actual
            return

        if expected != actual:
            yield path, expected, actual

    @staticmethod
    def _stable_list(value: list[Any]) -> bool:
        return all(isinstance(item, str | int | float | bool | None) for item in value)

    def _finding(
        self,
        *,
        baseline: Baseline,
        snapshot: StateSnapshot,
        resource_key: str,
        drift_type: DriftType,
        path: str,
        expected: Any,
        actual: Any,
    ) -> DriftFinding:
        resource_type = self._resource_type(resource_key, expected, actual)
        severity = self._severity(resource_type, drift_type, path)
        multiplier = {DriftType.ADDED: 1.1, DriftType.REMOVED: 1.25}.get(drift_type, 1.0)
        finding = DriftFinding(
            baseline_id=baseline.id,
            snapshot_id=snapshot.id,
            resource_key=resource_key,
            resource_type=resource_type,
            drift_type=drift_type,
            path=path,
            expected=expected,
            actual=actual,
            severity=severity,
        )
        finding.risk_score = round(min(100.0, finding.risk_score * multiplier), 2)
        return finding

    @staticmethod
    def _resource_type(resource_key: str, expected: Any, actual: Any) -> str:
        document = actual if isinstance(actual, dict) else expected
        if isinstance(document, dict) and "resource_type" in document:
            return str(document["resource_type"])
        if "::" in resource_key:
            parts = resource_key.split("::")
            if len(parts) >= 4:
                return parts[-2]
        return "custom"

    def _severity(self, resource_type: str, drift_type: DriftType, path: str) -> Severity:
        normalized_path = path.lower()
        if any(
            fnmatch.fnmatch(normalized_path, pattern.lower())
            for pattern in self.config.critical_paths
        ):
            return Severity.CRITICAL
        if any(
            fnmatch.fnmatch(normalized_path, pattern.lower()) for pattern in self.config.high_paths
        ):
            return Severity.HIGH
        if resource_type.lower() in {"iam", "security_group", "network", "user"}:
            return Severity.HIGH
        if drift_type in {DriftType.ADDED, DriftType.REMOVED}:
            return Severity.MEDIUM
        return Severity.LOW

    def _is_ignored(self, path: str) -> bool:
        return any(fnmatch.fnmatch(path, pattern) for pattern in self.config.ignored_paths)
