from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

trace: Any = None
Resource: Any = None
TracerProvider: Any = None
_OTEL_IMPORT_ERROR: Exception | None = None

try:
    from opentelemetry import trace as otel_trace
    from opentelemetry.sdk.resources import Resource as OtelResource
    from opentelemetry.sdk.trace import TracerProvider as OtelTracerProvider
except Exception as error:  # pragma: no cover - optional dependency guard
    _OTEL_IMPORT_ERROR = error
else:
    trace = otel_trace
    Resource = OtelResource
    TracerProvider = OtelTracerProvider


def configure_tracing(service_name: str) -> None:
    if trace is None or TracerProvider is None or Resource is None:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    trace.set_tracer_provider(provider)


@contextmanager
def span(name: str) -> Iterator[None]:
    if trace is None:
        yield
        return

    tracer = trace.get_tracer("drift_engine")
    with tracer.start_as_current_span(name):
        yield
