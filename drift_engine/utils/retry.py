from __future__ import annotations

import asyncio
import functools
import secrets
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


class RetryExhaustedError(RuntimeError):
    """Raised when a retry policy exhausts all attempts."""


def async_retry(
    *,
    attempts: int = 3,
    base_delay_seconds: float = 0.25,
    max_delay_seconds: float = 5.0,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_error: BaseException | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_on as error:
                    last_error = error
                    if attempt == attempts:
                        break
                    jitter = secrets.SystemRandom().uniform(0, base_delay_seconds)
                    delay = min(
                        max_delay_seconds, base_delay_seconds * (2 ** (attempt - 1)) + jitter
                    )
                    await asyncio.sleep(delay)
            raise RetryExhaustedError(
                f"{func.__name__} failed after {attempts} attempts"
            ) from last_error

        return wrapper

    return decorator
