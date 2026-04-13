from __future__ import annotations

from typing import Any

from drift_engine.utils.serialization import canonical_dumps


class RedisCache:
    def __init__(self, url: str, *, prefix: str = "drift") -> None:
        self.url = url
        self.prefix = prefix
        self._client: Any | None = None

    async def connect(self) -> None:
        from redis.asyncio import from_url

        self._client = from_url(self.url, decode_responses=True)

    async def get_json(self, key: str) -> str | None:
        client = await self._get_client()
        result = await client.get(self._key(key))
        return str(result) if result is not None else None

    async def set_json(self, key: str, value: object, ttl_seconds: int = 300) -> None:
        client = await self._get_client()
        await client.set(self._key(key), canonical_dumps(value), ex=ttl_seconds)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def _get_client(self) -> Any:
        if self._client is None:
            await self.connect()
        if self._client is None:
            raise RuntimeError("redis client was not initialized")
        return self._client
