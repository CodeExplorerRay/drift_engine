from __future__ import annotations

from drift_engine.core.baseline import BaselineManager
from drift_engine.core.drift_detector import DriftDetector, DriftDetectorConfig
from drift_engine.core.models import DriftType, StateSnapshot


def test_detects_modified_resource(
    expected_resources: dict[str, dict[str, object]],
    actual_resources: dict[str, dict[str, object]],
) -> None:
    baseline = BaselineManager().create(name="prod", resources=expected_resources)
    snapshot = StateSnapshot(source="test", resources=actual_resources)

    report = DriftDetector().detect(baseline, snapshot)

    assert report.summary.modified == 2
    assert {finding.path for finding in report.findings} == {"$.version", "$.active"}


def test_detects_added_and_removed_resources(
    expected_resources: dict[str, dict[str, object]],
) -> None:
    baseline = BaselineManager().create(name="prod", resources=expected_resources)
    snapshot = StateSnapshot(source="test", resources={})

    report = DriftDetector().detect(baseline, snapshot)

    assert report.summary.removed == 2
    assert {finding.drift_type for finding in report.findings} == {DriftType.REMOVED}


def test_ignored_paths_do_not_emit_findings(
    expected_resources: dict[str, dict[str, object]],
    actual_resources: dict[str, dict[str, object]],
) -> None:
    baseline = BaselineManager().create(name="prod", resources=expected_resources)
    snapshot = StateSnapshot(source="test", resources=actual_resources)

    report = DriftDetector(DriftDetectorConfig(ignored_paths={"$.version", "$.active"})).detect(
        baseline,
        snapshot,
    )

    assert report.findings == []
