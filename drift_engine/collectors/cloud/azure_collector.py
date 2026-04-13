from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from drift_engine.collectors.base import BaseCollector, CollectionContext, CollectorConfig
from drift_engine.core.models import StateSnapshot


class AzureCollector(BaseCollector):
    resource_type = "azure"

    def __init__(self, config: CollectorConfig | None = None) -> None:
        super().__init__("azure", config)

    async def collect(self, context: CollectionContext) -> StateSnapshot:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.resource import ResourceManagementClient
        except ImportError:
            return StateSnapshot(
                source=self.name,
                resources={},
                metadata={"enabled": False, "reason": "azure SDK is not installed"},
            )

        subscription_id = context.scope.get("azure_subscription_id") or self.config.settings.get(
            "subscription_id"
        )
        if not subscription_id:
            return StateSnapshot(
                source=self.name,
                resources={},
                metadata={"enabled": False, "reason": "azure_subscription_id not provided"},
            )

        credential = DefaultAzureCredential()
        client = ResourceManagementClient(credential, subscription_id)
        resources: dict[str, dict[str, Any]] = {}
        errors: list[str] = []
        try:
            for group in self._with_retries(lambda: client.resource_groups.list()):
                resources[
                    self.resource_key(
                        f"resource-group/{group.name}",
                        provider="azure",
                        account=subscription_id,
                        region=group.location,
                    )
                ] = self._resource_group_to_resource(group)
            for resource in self._with_retries(lambda: client.resources.list()):
                resources[
                    self.resource_key(
                        resource.id,
                        provider="azure",
                        account=subscription_id,
                        region=resource.location,
                    )
                ] = self._generic_resource_to_resource(resource)
        except Exception as error:
            errors.append(str(error))

        return StateSnapshot(source=self.name, resources=resources, metadata={"errors": errors})

    @staticmethod
    def _resource_group_to_resource(group: Any) -> dict[str, Any]:
        return {
            "resource_type": "azure_resource_group",
            "provider": "azure",
            "id": getattr(group, "id", None),
            "name": getattr(group, "name", None),
            "location": getattr(group, "location", None),
            "tags": getattr(group, "tags", None) or {},
            "provisioning_state": getattr(
                getattr(group, "properties", None),
                "provisioning_state",
                None,
            ),
        }

    @staticmethod
    def _generic_resource_to_resource(resource: Any) -> dict[str, Any]:
        return {
            "resource_type": "azure_resource",
            "provider": "azure",
            "id": resource.id,
            "name": resource.name,
            "type": resource.type,
            "location": resource.location,
            "tags": resource.tags or {},
            "managed_by": getattr(resource, "managed_by", None),
            "sku": getattr(resource, "sku", None),
        }

    @staticmethod
    def _with_retries(operation: Callable[[], Any], *, attempts: int = 3) -> Any:
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return operation()
            except Exception as error:
                last_error = error
                if attempt + 1 == attempts:
                    break
                time.sleep(0.2 * (2**attempt))
        raise RuntimeError("Azure collector operation failed") from last_error
