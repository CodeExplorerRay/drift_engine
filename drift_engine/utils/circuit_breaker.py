from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(RuntimeError):
    """Raised when a protected operation is blocked by an open circuit."""


@dataclass(slots=True)
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_seconds: float = 30.0
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    opened_at: float | None = None

    async def call(self, func: Callable[P, Awaitable[T]], *args: P.args, **kwargs: P.kwargs) -> T:
        if self.state == CircuitState.OPEN:
            if (
                self.opened_at is None
                or (time.monotonic() - self.opened_at) < self.recovery_seconds
            ):
                raise CircuitOpenError("circuit is open")
            self.state = CircuitState.HALF_OPEN

        try:
            result = await func(*args, **kwargs)
        except Exception:
            self._record_failure()
            raise

        self._record_success()
        return result

    def _record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = time.monotonic()

    def _record_success(self) -> None:
        self.failures = 0
        self.opened_at = None
        self.state = CircuitState.CLOSED
