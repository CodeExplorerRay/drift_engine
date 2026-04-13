from __future__ import annotations

from drift_engine.core.engine import DriftEngine


async def test_engine_runs_collect_detect_policy_cycle(
    engine: DriftEngine,
    expected_resources: dict[str, dict[str, object]],
) -> None:
    baseline = engine.baseline_manager.create(name="prod", resources=expected_resources)
    await engine.baselines.save(baseline)

    result = await engine.run_once(baseline_id=baseline.id, collector_names=["static"])

    assert result.report.summary.modified == 2
    assert result.report.risk_score > 0
    assert await engine.reports.get(result.report.id) is not None
