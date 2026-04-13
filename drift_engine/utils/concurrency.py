from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Iterable
from typing import TypeVar

T = TypeVar("T")


async def gather_limited(limit: int, coroutines: Iterable[Awaitable[T]]) -> list[T]:
    if limit < 1:
        raise ValueError("limit must be at least 1")

    semaphore = asyncio.Semaphore(limit)

    async def run(coro: Awaitable[T]) -> T:
        async with semaphore:
            return await coro

    return await asyncio.gather(*(run(coro) for coro in coroutines))


async def cancel_and_wait(tasks: Iterable[asyncio.Task[object]]) -> None:
    pending = [task for task in tasks if not task.done()]
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)
