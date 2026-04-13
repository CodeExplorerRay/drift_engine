from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from drift_engine.core.models import ResourceIdentity, StateSnapshot


@dataclass(slots=True)
class CollectorConfig:
    enabled: bool = True
    timeout_seconds: float = 30.0
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CollectionContext:
    scope: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    deadline_seconds: float | None = None


class BaseCollector(ABC):
    """Base class for pluggable state collectors."""

    resource_type = "custom"

    def __init__(self, name: str, config: CollectorConfig | None = None) -> None:
        self.name = name
        self.config = config or CollectorConfig()

    @abstractmethod
    async def collect(self, context: CollectionContext) -> StateSnapshot:
        raise NotImplementedError

    def resource_key(
        self,
        resource_id: str,
        *,
        provider: str = "local",
        account: str | None = None,
        region: str | None = None,
    ) -> str:
        return ResourceIdentity(
            provider=provider,
            account=account,
            region=region,
            resource_type=self.resource_type,
            resource_id=resource_id,
        ).key

    @staticmethod
    async def run_command(
        *command: str,
        timeout_seconds: float = 15.0,
    ) -> tuple[int, str, str]:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
        except TimeoutError as error:
            process.kill()
            await process.wait()
            raise TimeoutError(f"command timed out: {' '.join(command)}") from error
        return_code = process.returncode if process.returncode is not None else -1
        return (
            return_code,
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
        )


class StaticCollector(BaseCollector):
    """Deterministic collector used by tests and controlled integrations."""

    def __init__(self, name: str, resources: dict[str, dict[str, Any]]) -> None:
        super().__init__(name)
        self.resources = resources

    async def collect(self, context: CollectionContext) -> StateSnapshot:
        return StateSnapshot(source=self.name, resources=self.resources, metadata=context.metadata)
