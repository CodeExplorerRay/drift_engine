from __future__ import annotations

from typing import Any


class ElasticsearchStore:
    def __init__(self, url: str, *, index_prefix: str = "drift") -> None:
        self.url = url
        self.index_prefix = index_prefix
        self._client: Any | None = None

    async def connect(self) -> None:
        from elasticsearch import AsyncElasticsearch

        self._client = AsyncElasticsearch(self.url)

    async def index_report(self, report: dict[str, Any]) -> None:
        client = await self._get_client()
        await client.index(
            index=f"{self.index_prefix}-reports",
            id=report["id"],
            document=report,
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def _get_client(self) -> Any:
        if self._client is None:
            await self.connect()
        if self._client is None:
            raise RuntimeError("elasticsearch client was not initialized")
        return self._client
