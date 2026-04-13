from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

Counter: Any = None
Gauge: Any = None
Histogram: Any = None
_PROMETHEUS_IMPORT_ERROR: Exception | None = None

try:
    from prometheus_client import Counter as PrometheusCounter
    from prometheus_client import Gauge as PrometheusGauge
    from prometheus_client import Histogram as PrometheusHistogram
except Exception as error:  # pragma: no cover - optional dependency guard
    _PROMETHEUS_IMPORT_ERROR = error
else:
    Counter = PrometheusCounter
    Gauge = PrometheusGauge
    Histogram = PrometheusHistogram


@dataclass(slots=True)
class MetricsRecorder:
    enabled: bool = True
    _noop: bool = field(init=False, default=True)
    engine_runs: Any = field(init=False, default=None)
    findings: Any = field(init=False, default=None)
    run_duration: Any = field(init=False, default=None)
    collector_duration: Any = field(init=False, default=None)
    current_risk: Any = field(init=False, default=None)

    def __post_init__(self) -> None:
        if not self.enabled or Counter is None:
            self._noop = True
            return

        self._noop = False
        self.engine_runs = Counter(
            "drift_engine_runs_total",
            "Total drift engine runs.",
            ["status"],
        )
        self.findings = Counter(
            "drift_findings_total",
            "Total drift findings detected.",
            ["severity", "drift_type"],
        )
        self.run_duration = Histogram(
            "drift_engine_run_duration_seconds",
            "Duration of complete drift engine runs.",
        )
        self.collector_duration = Histogram(
            "drift_collector_duration_seconds",
            "Duration of collector runs.",
            ["collector"],
        )
        self.current_risk = Gauge(
            "drift_current_risk_score",
            "Most recent aggregate risk score.",
        )

    def record_run(self, status: str, risk_score: float | None = None) -> None:
        if self._noop:
            return
        self.engine_runs.labels(status=status).inc()
        if risk_score is not None:
            self.current_risk.set(risk_score)

    def record_finding(self, severity: str, drift_type: str) -> None:
        if not self._noop:
            self.findings.labels(severity=severity, drift_type=drift_type).inc()

    @contextmanager
    def time_run(self) -> Iterator[None]:
        start = perf_counter()
        try:
            yield
        finally:
            if not self._noop:
                self.run_duration.observe(perf_counter() - start)

    @contextmanager
    def time_collector(self, collector: str) -> Iterator[None]:
        start = perf_counter()
        try:
            yield
        finally:
            if not self._noop:
                self.collector_duration.labels(collector=collector).observe(perf_counter() - start)


metrics = MetricsRecorder(enabled=False)
