from __future__ import annotations

from dataclasses import dataclass, field
from types import TracebackType

from drift_engine.storage.base import (
    BaselineRepository,
    DriftReportRepository,
    InMemoryBaselineRepository,
    InMemoryDriftReportRepository,
    InMemoryPolicyRepository,
    InMemorySnapshotRepository,
    PolicyRepository,
    SnapshotRepository,
)


class UnitOfWork:
    baselines: BaselineRepository
    snapshots: SnapshotRepository
    reports: DriftReportRepository
    policies: PolicyRepository

    async def __aenter__(self) -> UnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    async def commit(self) -> None:
        raise NotImplementedError

    async def rollback(self) -> None:
        raise NotImplementedError


@dataclass(slots=True)
class InMemoryUnitOfWork(UnitOfWork):
    baselines: BaselineRepository = field(default_factory=InMemoryBaselineRepository)
    snapshots: SnapshotRepository = field(default_factory=InMemorySnapshotRepository)
    reports: DriftReportRepository = field(default_factory=InMemoryDriftReportRepository)
    policies: PolicyRepository = field(default_factory=InMemoryPolicyRepository)

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None
