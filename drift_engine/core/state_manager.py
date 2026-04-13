from __future__ import annotations

from collections.abc import Iterable
from time import perf_counter
from typing import Any

from config.logging_config import get_logger
from drift_engine.collectors.base import BaseCollector, CollectionContext
from drift_engine.core.models import CollectorResult, CollectorStatus, StateSnapshot
from drift_engine.telemetry.metrics import MetricsRecorder
from drift_engine.utils.concurrency import gather_limited

logger = get_logger(__name__)


class StateManager:
    """Coordinates collectors and merges their outputs into one snapshot."""

    def __init__(
        self,
        collectors: Iterable[BaseCollector],
        *,
        concurrency: int = 8,
        metrics: MetricsRecorder | None = None,
    ) -> None:
        self.collectors = list(collectors)
        self.concurrency = concurrency
        self.metrics = metrics or MetricsRecorder(enabled=False)

    async def collect(
        self, context: CollectionContext | None = None
    ) -> tuple[StateSnapshot, list[CollectorResult]]:
        context = context or CollectionContext()
        results = await gather_limited(
            self.concurrency,
            (self._run_collector(collector, context) for collector in self.collectors),
        )
        resources: dict[str, dict[str, Any]] = {}
        errors: list[str] = []
        metadata: dict[str, Any] = {"collectors": []}

        for result in results:
            metadata["collectors"].append(
                {
                    "name": result.collector_name,
                    "status": result.status.value,
                    "duration_ms": result.duration_ms,
                    "errors": result.errors,
                }
            )
            if result.errors:
                errors.extend(result.errors)
            if result.snapshot:
                resources.update(result.snapshot.resources)

        snapshot = StateSnapshot(
            source="composite",
            resources=resources,
            metadata={"status": "partial" if errors else "success", "errors": errors, **metadata},
        )
        return snapshot, results

    async def _run_collector(
        self, collector: BaseCollector, context: CollectionContext
    ) -> CollectorResult:
        start = perf_counter()
        try:
            with self.metrics.time_collector(collector.name):
                snapshot = await collector.collect(context)
            duration_ms = (perf_counter() - start) * 1000
            status = (
                CollectorStatus.PARTIAL
                if snapshot.metadata.get("errors")
                else CollectorStatus.SUCCESS
            )
            return CollectorResult(
                collector_name=collector.name,
                status=status,
                snapshot=snapshot,
                duration_ms=round(duration_ms, 2),
                errors=[str(error) for error in snapshot.metadata.get("errors", [])],
            )
        except Exception as error:
            duration_ms = (perf_counter() - start) * 1000
            logger.exception("collector_failed", collector=collector.name, error=str(error))
            return CollectorResult(
                collector_name=collector.name,
                status=CollectorStatus.FAILED,
                duration_ms=round(duration_ms, 2),
                errors=[str(error)],
            )
