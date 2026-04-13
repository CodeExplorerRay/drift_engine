from __future__ import annotations

from importlib import metadata

from drift_engine.collectors.base import BaseCollector, CollectionContext, CollectorConfig
from drift_engine.core.models import StateSnapshot


class PackageCollector(BaseCollector):
    resource_type = "package"

    def __init__(self, config: CollectorConfig | None = None) -> None:
        super().__init__("package", config)

    async def collect(self, context: CollectionContext) -> StateSnapshot:
        include_prefixes = tuple(context.scope.get("package_prefixes") or ())
        resources: dict[str, dict[str, object]] = {}

        for distribution in metadata.distributions():
            name = distribution.metadata["Name"] or distribution.name
            if include_prefixes and not name.lower().startswith(include_prefixes):
                continue
            resources[self.resource_key(name)] = {
                "resource_type": self.resource_type,
                "name": name,
                "version": distribution.version,
                "installer": distribution.read_text("INSTALLER") or "unknown",
            }

        return StateSnapshot(
            source=self.name,
            resources=resources,
            metadata={"ecosystem": "python", "count": len(resources)},
        )
