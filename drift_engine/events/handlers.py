from __future__ import annotations

from collections.abc import Awaitable, Callable

from config.logging_config import get_logger
from drift_engine.events.models import Event
from drift_engine.telemetry.metrics import MetricsRecorder

logger = get_logger(__name__)


async def log_event(event: Event) -> None:
    logger.info(
        "domain_event",
        event_id=event.id,
        event_type=event.type.value,
        subject=event.subject,
        correlation_id=event.correlation_id,
    )


def metrics_event_handler(metrics: MetricsRecorder) -> Callable[[Event], Awaitable[None]]:
    async def handle(event: Event) -> None:
        del event
        metrics.record_run("event")

    return handle
