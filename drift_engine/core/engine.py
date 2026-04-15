from __future__ import annotations

from typing import Any

from config.logging_config import get_logger
from drift_engine.collectors.base import CollectionContext
from drift_engine.collectors.registry import CollectorRegistry
from drift_engine.core.baseline import BaselineManager
from drift_engine.core.drift_detector import DriftDetector
from drift_engine.core.exceptions import BaselineNotFoundError
from drift_engine.core.models import (
    Baseline,
    CollectorResult,
    CollectorStatus,
    DriftReport,
    DriftType,
    EngineRunResult,
    ScanCompleteness,
    StateSnapshot,
)
from drift_engine.events.bus import EventBus
from drift_engine.events.models import Event, EventType
from drift_engine.policies.engine import PolicyEngine
from drift_engine.remediation.engine import RemediationEngine
from drift_engine.storage.base import (
    AuditRepository,
    BaselineRepository,
    DriftReportRepository,
    JobRepository,
    PolicyRepository,
    RemediationRepository,
    SnapshotRepository,
)
from drift_engine.telemetry.metrics import MetricsRecorder
from drift_engine.telemetry.tracing import span

logger = get_logger(__name__)


class DriftEngine:
    """High-level orchestration for collect, detect, evaluate, and remediate."""

    def __init__(
        self,
        *,
        collectors: CollectorRegistry,
        baselines: BaselineRepository,
        snapshots: SnapshotRepository,
        reports: DriftReportRepository,
        baseline_manager: BaselineManager | None = None,
        detector: DriftDetector | None = None,
        policies: PolicyEngine | None = None,
        policy_repository: PolicyRepository | None = None,
        audit_repository: AuditRepository | None = None,
        job_repository: JobRepository | None = None,
        remediation_repository: RemediationRepository | None = None,
        remediation: RemediationEngine | None = None,
        events: EventBus | None = None,
        metrics: MetricsRecorder | None = None,
    ) -> None:
        self.collectors = collectors
        self.baselines = baselines
        self.snapshots = snapshots
        self.reports = reports
        self.baseline_manager = baseline_manager or BaselineManager()
        self.detector = detector or DriftDetector()
        self.policies = policies or PolicyEngine.default()
        self.policy_repository = policy_repository
        self.audit_repository = audit_repository
        self.job_repository = job_repository
        self.remediation_repository = remediation_repository
        self.remediation = remediation
        self.events = events or EventBus()
        self.metrics = metrics or MetricsRecorder(enabled=False)

    async def collect_state(
        self,
        *,
        collector_names: list[str] | None = None,
        context: CollectionContext | None = None,
    ) -> tuple[StateSnapshot, list[Any]]:
        with span("drift.collect_state"):
            selected = self.collectors.select(collector_names)
            from drift_engine.core.state_manager import StateManager

            manager = StateManager(selected, metrics=self.metrics)
            snapshot, results = await manager.collect(context)
            await self.snapshots.save(snapshot)
            await self.events.publish(
                Event(
                    type=EventType.SNAPSHOT_COLLECTED,
                    subject=snapshot.id,
                    payload=snapshot.to_document(),
                )
            )
            return snapshot, results

    async def create_baseline_from_current_state(
        self,
        *,
        name: str,
        version: str = "1.0.0",
        collector_names: list[str] | None = None,
        context: CollectionContext | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Baseline:
        snapshot, _ = await self.collect_state(collector_names=collector_names, context=context)
        baseline = self.baseline_manager.from_snapshot(
            name=name,
            snapshot=snapshot,
            version=version,
            metadata=metadata,
        )
        await self.baselines.save(baseline)
        await self.events.publish(
            Event(
                type=EventType.BASELINE_CREATED,
                subject=baseline.id,
                payload=baseline.to_document(),
            )
        )
        return baseline

    async def run_once(
        self,
        *,
        baseline_id: str,
        collector_names: list[str] | None = None,
        auto_remediate: bool = False,
        context: CollectionContext | None = None,
    ) -> EngineRunResult:
        with self.metrics.time_run(), span("drift.run_once"):
            baseline = await self.baselines.get(baseline_id)
            if baseline is None:
                raise BaselineNotFoundError(f"baseline {baseline_id!r} not found")

            if self.baseline_manager.repair_legacy_signature(baseline):
                await self.baselines.save(baseline)
                logger.warning(
                    "baseline_signature_repaired",
                    baseline_id=baseline.id,
                    baseline_name=baseline.name,
                )
            self.baseline_manager.verify(baseline)
            snapshot, collector_results = await self.collect_state(
                collector_names=collector_names,
                context=context,
            )
            report = self.detector.detect(baseline, snapshot)
            policy_result = self.policies.evaluate_report(
                report, snapshot=snapshot, baseline=baseline
            )
            report.policy_results = [policy_result.to_document()]
            self.policies.apply_risk(report, policy_result)
            self._apply_scan_integrity(report, collector_results)

            for finding in report.findings:
                self.metrics.record_finding(finding.severity.value, finding.drift_type.value)

            remediations: list[dict[str, Any]] = []
            if auto_remediate and self.remediation is not None:
                plan = self.remediation.plan(report)
                execution = await self.remediation.execute(plan)
                remediations = [item.to_document() for item in execution]

            await self.reports.save(report)
            self.metrics.record_run("success", report.risk_score)
            await self.events.publish(
                Event(
                    type=EventType.DRIFT_DETECTED if report.findings else EventType.NO_DRIFT,
                    subject=report.id,
                    payload=report.to_document(),
                )
            )
            logger.info(
                "drift_run_completed",
                baseline_id=baseline.id,
                report_id=report.id,
                findings=len(report.findings),
                risk_score=report.risk_score,
            )
            return EngineRunResult(
                baseline=baseline,
                snapshot=snapshot,
                report=report,
                collector_results=collector_results,
                remediations=remediations,
            )

    @staticmethod
    def _apply_scan_integrity(
        report: DriftReport, collector_results: list[CollectorResult]
    ) -> None:
        degraded_collectors = [
            result
            for result in collector_results
            if result.status in {CollectorStatus.FAILED, CollectorStatus.PARTIAL}
        ]
        report.collector_results = [result.to_document() for result in collector_results]
        if not degraded_collectors:
            report.scan_completeness = ScanCompleteness.COMPLETE
            return

        report.scan_completeness = ScanCompleteness.PARTIAL
        report.integrity_warnings = [
            (
                "scan is partial; one or more collectors failed or returned incomplete data, "
                "so removed-resource findings may be untrusted"
            )
        ]
        for finding in report.findings:
            if finding.drift_type != DriftType.REMOVED:
                continue
            finding.trusted = False
            finding.integrity_notes.append(
                "removed finding came from a partial scan and is not authoritative"
            )
            finding.risk_score = 0.0
        trusted_findings = [finding for finding in report.findings if finding.trusted]
        report.summary = report.build_summary(report.findings)
        report.risk_score = report.aggregate_risk(trusted_findings)
