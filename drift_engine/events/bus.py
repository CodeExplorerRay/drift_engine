from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable

from config.logging_config import get_logger
from drift_engine.events.models import Event, EventType

logger = get_logger(__name__)

EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    """In-process async event bus with fan-out and error isolation."""

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._wildcard_handlers: list[EventHandler] = []

    def subscribe(self, event_type: EventType | None, handler: EventHandler) -> None:
        if event_type is None:
            self._wildcard_handlers.append(handler)
        else:
            self._handlers[event_type].append(handler)

    async def publish(self, event: Event) -> None:
        handlers = [*self._wildcard_handlers, *self._handlers[event.type]]
        if not handlers:
            return
        results = await asyncio.gather(
            *(handler(event) for handler in handlers), return_exceptions=True
        )
        for result in results:
            if isinstance(result, Exception):
                logger.exception(
                    "event_handler_failed", event_type=event.type.value, error=str(result)
                )
