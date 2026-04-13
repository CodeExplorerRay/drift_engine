from __future__ import annotations

import importlib.util
import shutil
from typing import Any

from config.settings import Settings
from drift_engine.integrations.models import IntegrationDescriptor, IntegrationStatus


def build_integration_catalog(settings: Settings) -> list[IntegrationDescriptor]:
    """Return externally configurable integrations and their local readiness state."""

    enabled = settings.enabled_integration_names
    return [
        _kubernetes_descriptor(settings, enabled=enabled),
        _aws_descriptor(settings, enabled=enabled),
        _azure_descriptor(settings, enabled=enabled),
    ]


def _kubernetes_descriptor(settings: Settings, *, enabled: set[str]) -> IntegrationDescriptor:
    missing = []
    if shutil.which("kubectl") is None:
        missing.append("kubectl")
    status = _status(enabled="kubernetes" in enabled, missing=missing)
    namespaces = settings.kubernetes_namespace_values
    return IntegrationDescriptor(
        name="kubernetes",
        display_name="Kubernetes",
        collector_name="kubernetes",
        description=(
            "Collects namespaces, workloads, services, ingresses, configmaps, and pods through "
            "the active kubectl context."
        ),
        enabled="kubernetes" in enabled,
        status=status,
        resource_types=[
            "namespaces",
            "deployments",
            "daemonsets",
            "statefulsets",
            "services",
            "ingresses",
            "configmaps",
            "pods",
        ],
        optional_dependencies=["kubectl"],
        missing=missing,
        settings={"namespaces": namespaces},
        setup_hint=(
            "Install kubectl, authenticate to the target cluster, then set "
            "DRIFT_ENABLED_INTEGRATIONS=kubernetes. Optionally set "
            "DRIFT_KUBERNETES_NAMESPACES=prod,platform."
        ),
    )


def _aws_descriptor(settings: Settings, *, enabled: set[str]) -> IntegrationDescriptor:
    missing = []
    if not _module_available("boto3"):
        missing.append("boto3")
    status = _status(enabled="aws" in enabled, missing=missing)
    return IntegrationDescriptor(
        name="aws",
        display_name="AWS",
        collector_name="aws",
        description=(
            "Collects EC2 security groups and S3 bucket inventory through the standard AWS "
            "credential provider chain."
        ),
        enabled="aws" in enabled,
        status=status,
        resource_types=["security_groups", "s3_buckets"],
        optional_dependencies=["system-drift-engine[aws]", "boto3"],
        missing=missing,
        settings={
            "regions": settings.aws_region_values,
            "collect_s3_buckets": settings.aws_collect_s3_buckets,
        },
        setup_hint=(
            "Install the aws extra, provide AWS credentials through environment, profile, or IAM "
            "role, then set DRIFT_ENABLED_INTEGRATIONS=aws and DRIFT_AWS_REGIONS."
        ),
    )


def _azure_descriptor(settings: Settings, *, enabled: set[str]) -> IntegrationDescriptor:
    missing = []
    if not _module_available("azure.identity"):
        missing.append("azure-identity")
    if not _module_available("azure.mgmt.resource"):
        missing.append("azure-mgmt-resource")
    if not settings.azure_subscription_id:
        missing.append("DRIFT_AZURE_SUBSCRIPTION_ID")
    status = _status(enabled="azure" in enabled, missing=missing)
    return IntegrationDescriptor(
        name="azure",
        display_name="Azure",
        collector_name="azure",
        description=(
            "Collects Azure resource groups and generic Azure resources through "
            "DefaultAzureCredential."
        ),
        enabled="azure" in enabled,
        status=status,
        resource_types=["resource_groups", "resources"],
        optional_dependencies=["system-drift-engine[azure]", "azure-identity"],
        required_configuration=["DRIFT_AZURE_SUBSCRIPTION_ID"],
        missing=missing,
        settings={"subscription_id_configured": bool(settings.azure_subscription_id)},
        setup_hint=(
            "Install the azure extra, authenticate with az login, workload identity, or managed "
            "identity, then set DRIFT_ENABLED_INTEGRATIONS=azure and "
            "DRIFT_AZURE_SUBSCRIPTION_ID."
        ),
    )


def _status(*, enabled: bool, missing: list[str]) -> IntegrationStatus:
    if not enabled:
        return "disabled"
    if missing:
        config_missing = any(item.startswith("DRIFT_") for item in missing)
        return "needs_configuration" if config_missing else "missing_dependency"
    return "ready"


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def integration_settings(settings: Settings, integration_name: str) -> dict[str, Any]:
    if integration_name == "kubernetes":
        return {"namespaces": settings.kubernetes_namespace_values}
    if integration_name == "aws":
        return {
            "regions": settings.aws_region_values,
            "collect_s3_buckets": settings.aws_collect_s3_buckets,
        }
    if integration_name == "azure":
        return {"subscription_id": settings.azure_subscription_id}
    return {}
