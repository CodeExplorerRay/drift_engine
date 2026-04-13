from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from drift_engine.collectors.base import BaseCollector, CollectorConfig
from drift_engine.collectors.cloud.aws_collector import AWSCollector
from drift_engine.collectors.cloud.azure_collector import AzureCollector
from drift_engine.collectors.file_collector import FileCollector, default_file_paths
from drift_engine.collectors.kubernetes_collector import KubernetesCollector
from drift_engine.collectors.network_collector import NetworkCollector
from drift_engine.collectors.package_collector import PackageCollector
from drift_engine.collectors.service_collector import ServiceCollector
from drift_engine.collectors.user_collector import UserCollector


class CollectorRegistry:
    """Runtime registry for collector plugins."""

    def __init__(self, collectors: Iterable[BaseCollector] | None = None) -> None:
        self._collectors: dict[str, BaseCollector] = {}
        for collector in collectors or []:
            self.register(collector)

    def register(self, collector: BaseCollector) -> None:
        if collector.name in self._collectors:
            raise ValueError(f"collector {collector.name!r} already registered")
        self._collectors[collector.name] = collector

    def get(self, name: str) -> BaseCollector:
        try:
            return self._collectors[name]
        except KeyError as error:
            raise KeyError(f"collector {name!r} is not registered") from error

    def names(self) -> list[str]:
        return sorted(self._collectors)

    def select(self, names: list[str] | None = None) -> list[BaseCollector]:
        selected_names = names or self.names()
        return [self.get(name) for name in selected_names if self.get(name).config.enabled]

    @classmethod
    def default(cls, settings: Any | None = None) -> CollectorRegistry:
        registry = cls()
        enabled_integrations = (
            settings.enabled_integration_names if settings is not None else set()
        )
        default_timeout = CollectorConfig().timeout_seconds
        timeout_seconds = (
            settings.collector_timeout_seconds if settings is not None else default_timeout
        )
        aws_regions = (
            settings.aws_region_values if settings is not None else ["us-east-1"]
        )
        registry.register(FileCollector(CollectorConfig(settings={"paths": default_file_paths()})))
        registry.register(PackageCollector())
        registry.register(ServiceCollector())
        registry.register(NetworkCollector())
        registry.register(UserCollector())
        registry.register(
            KubernetesCollector(
                CollectorConfig(
                    enabled="kubernetes" in enabled_integrations,
                    timeout_seconds=timeout_seconds,
                    settings={
                        "namespaces": settings.kubernetes_namespace_values
                        if settings is not None
                        else []
                    },
                )
            )
        )
        registry.register(
            AWSCollector(
                CollectorConfig(
                    enabled="aws" in enabled_integrations,
                    timeout_seconds=timeout_seconds,
                    settings={
                        "regions": aws_regions,
                        "collect_s3_buckets": settings.aws_collect_s3_buckets
                        if settings is not None
                        else True,
                    },
                )
            )
        )
        registry.register(
            AzureCollector(
                CollectorConfig(
                    enabled="azure" in enabled_integrations,
                    timeout_seconds=timeout_seconds,
                    settings={
                        "subscription_id": settings.azure_subscription_id
                        if settings is not None
                        else None
                    },
                )
            )
        )
        return registry
