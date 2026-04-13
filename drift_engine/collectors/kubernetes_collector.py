from __future__ import annotations

import json
from typing import Any, ClassVar

from drift_engine.collectors.base import BaseCollector, CollectionContext, CollectorConfig
from drift_engine.core.models import StateSnapshot


class KubernetesCollector(BaseCollector):
    resource_type = "kubernetes"
    CLUSTER_SCOPED_KINDS: ClassVar[set[str]] = {
        "namespaces",
        "clusterroles",
        "clusterrolebindings",
    }

    def __init__(self, config: CollectorConfig | None = None) -> None:
        super().__init__("kubernetes", config)

    async def collect(self, context: CollectionContext) -> StateSnapshot:
        namespaces = context.scope.get("kubernetes_namespaces") or self.config.settings.get(
            "namespaces"
        )
        resources: dict[str, dict[str, Any]] = {}
        errors: list[str] = []
        for kind in self._resource_kinds():
            for namespace_args in self._namespace_args(kind, namespaces):
                try:
                    code, stdout, stderr = await self.run_command(
                        "kubectl",
                        "get",
                        kind,
                        *namespace_args,
                        "-o",
                        "json",
                        timeout_seconds=self.config.timeout_seconds,
                    )
                except (FileNotFoundError, TimeoutError) as error:
                    errors.append(str(error))
                    break
                if code != 0:
                    errors.append(stderr.strip() or f"{kind}: kubectl exited {code}")
                    continue
                try:
                    resources.update(self._parse(kind, stdout))
                except json.JSONDecodeError as error:
                    errors.append(f"{kind}: invalid json: {error}")

        return StateSnapshot(
            source=self.name,
            resources=resources,
            metadata={
                "errors": errors,
                "namespaces": [str(item) for item in namespaces] if namespaces else [],
            },
        )

    @staticmethod
    def _resource_kinds() -> tuple[str, ...]:
        return (
            "namespaces",
            "deployments",
            "daemonsets",
            "statefulsets",
            "services",
            "ingresses",
            "configmaps",
            "serviceaccounts",
            "roles",
            "rolebindings",
            "clusterroles",
            "clusterrolebindings",
            "pods",
        )

    def _namespace_args(self, kind: str, namespaces: Any) -> list[list[str]]:
        if kind in self.CLUSTER_SCOPED_KINDS:
            return [[]]
        if namespaces:
            return [["--namespace", str(namespace)] for namespace in namespaces]
        return [["--all-namespaces"]]

    def _parse(self, kind: str, stdout: str) -> dict[str, dict[str, Any]]:
        payload = json.loads(stdout)
        resources: dict[str, dict[str, Any]] = {}
        for item in payload.get("items", []):
            api_version = item.get("apiVersion", "")
            metadata = item.get("metadata", {})
            namespace = metadata.get("namespace") or "cluster"
            name = metadata.get("name", "unknown")
            key = self.resource_key(f"{namespace}/{kind}/{name}", provider="kubernetes")
            resources[key] = {
                "resource_type": self.resource_type,
                "kind": kind,
                "namespace": namespace,
                "name": name,
                "api_version": api_version,
                "labels": metadata.get("labels", {}),
                "annotations": metadata.get("annotations", {}),
                "owner_references": metadata.get("ownerReferences", []),
                "spec": item.get("spec", {}),
                "status": item.get("status", {}),
            }
        return resources
