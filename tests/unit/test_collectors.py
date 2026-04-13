from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from config.settings import Settings
from drift_engine.collectors.base import BaseCollector, StaticCollector
from drift_engine.collectors.cloud.aws_collector import AWSCollector
from drift_engine.collectors.cloud.azure_collector import AzureCollector
from drift_engine.collectors.kubernetes_collector import KubernetesCollector
from drift_engine.collectors.network_collector import NetworkCollector
from drift_engine.collectors.registry import CollectorRegistry
from drift_engine.collectors.service_collector import ServiceCollector
from drift_engine.core.state_manager import StateManager
from drift_engine.integrations.kubernetes import KubernetesIntegrationChecker
from drift_engine.integrations.registry import build_integration_catalog


async def test_state_manager_merges_static_collectors() -> None:
    manager = StateManager(
        [
            StaticCollector("one", {"local::_::_::file::/etc/a": {"resource_type": "file"}}),
            StaticCollector("two", {"local::_::_::service::sshd": {"resource_type": "service"}}),
        ]
    )

    snapshot, results = await manager.collect()

    assert len(results) == 2
    assert len(snapshot.resources) == 2
    assert snapshot.metadata["status"] == "success"


def test_windows_services_are_normalized() -> None:
    resources = ServiceCollector()._parse_windows_services(
        json.dumps(
            [
                {"Name": "Spooler", "Status": "Running", "StartType": "Automatic"},
                {"Name": "WinRM", "Status": "Stopped", "StartType": "Manual"},
            ]
        )
    )

    assert resources["local::_::_::service::Spooler"]["status"] == "Running"
    assert resources["local::_::_::service::WinRM"]["start_type"] == "Manual"
    assert "raw_json" not in resources["local::_::_::service::Spooler"]


def test_network_listeners_are_normalized() -> None:
    resources = NetworkCollector()._parse_listeners(
        "netstat",
        "\n".join(
            [
                "Proto Local Address Foreign Address State PID",
                "TCP 0.0.0.0:8080 0.0.0.0:0 LISTENING 100",
                "UDP 0.0.0.0:53 *:* 101",
            ]
        ),
    )

    tcp = resources["local::_::_::network::listener/tcp/0.0.0.0:8080"]
    udp = resources["local::_::_::network::listener/udp/0.0.0.0:53"]
    assert tcp["state"] == "LISTENING"
    assert tcp["pid"] == "100"
    assert udp["protocol"] == "udp"


def test_kubernetes_collector_parses_expanded_fixture() -> None:
    payload = {
        "items": [
            {
                "apiVersion": "apps/v1",
                "metadata": {
                    "namespace": "ops",
                    "name": "drift-engine",
                    "labels": {"app": "drift"},
                },
                "spec": {"replicas": 2},
                "status": {"readyReplicas": 2},
            }
        ]
    }

    resources = KubernetesCollector()._parse("deployments", json.dumps(payload))

    resource = resources["kubernetes::_::_::kubernetes::ops/deployments/drift-engine"]
    assert resource["api_version"] == "apps/v1"
    assert resource["spec"] == {"replicas": 2}
    assert resource["status"] == {"readyReplicas": 2}


def test_kubernetes_collector_scopes_all_selected_namespaces() -> None:
    collector = KubernetesCollector()

    args = collector._namespace_args("deployments", ["prod", "platform"])

    assert args == [["--namespace", "prod"], ["--namespace", "platform"]]
    assert collector._namespace_args("namespaces", ["prod"]) == [[]]
    assert collector._namespace_args("deployments", []) == [["--all-namespaces"]]


def test_aws_security_group_parser_preserves_policy_shape() -> None:
    resource = AWSCollector._security_group_to_resource(
        {
            "GroupId": "sg-123",
            "GroupName": "web",
            "Description": "web ingress",
            "VpcId": "vpc-123",
            "IpPermissions": [{"FromPort": 443}],
            "IpPermissionsEgress": [],
            "Tags": [{"Key": "env", "Value": "prod"}],
        },
        region="us-east-1",
    )

    assert resource["resource_type"] == "security_group"
    assert resource["group_id"] == "sg-123"
    assert resource["ingress"] == [{"FromPort": 443}]


def test_azure_resource_group_parser_preserves_tags() -> None:
    group = SimpleNamespace(
        id="/subscriptions/sub/resourceGroups/rg-prod",
        name="rg-prod",
        location="eastus",
        tags={"env": "prod"},
        properties=SimpleNamespace(provisioning_state="Succeeded"),
    )

    resource = AzureCollector._resource_group_to_resource(group)

    assert resource["resource_type"] == "azure_resource_group"
    assert resource["tags"] == {"env": "prod"}
    assert resource["provisioning_state"] == "Succeeded"


def test_registry_enables_external_integrations_from_settings() -> None:
    settings = Settings(
        enabled_integrations="kubernetes,aws,azure",
        kubernetes_namespaces="prod,platform",
        aws_regions="us-east-1,us-west-2",
        azure_subscription_id="sub-123",
    )

    registry = CollectorRegistry.default(settings)

    assert registry.get("kubernetes").config.enabled is True
    assert registry.get("kubernetes").config.settings["namespaces"] == ["prod", "platform"]
    assert registry.get("aws").config.enabled is True
    assert registry.get("aws").config.settings["regions"] == ["us-east-1", "us-west-2"]
    assert registry.get("azure").config.enabled is True
    assert registry.get("azure").config.settings["subscription_id"] == "sub-123"


def test_integration_catalog_reports_configuration_status() -> None:
    settings = Settings(enabled_integrations="azure")

    catalog = {item.name: item for item in build_integration_catalog(settings)}

    assert catalog["kubernetes"].status == "disabled"
    assert catalog["aws"].status == "disabled"
    assert catalog["azure"].enabled is True
    assert "DRIFT_AZURE_SUBSCRIPTION_ID" in catalog["azure"].missing


async def test_kubernetes_integration_checker_reports_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_which(command: str) -> str | None:
        return "kubectl" if command == "kubectl" else None

    async def fake_run_command(
        *command: str,
        timeout_seconds: float = 15.0,
    ) -> tuple[int, str, str]:
        del timeout_seconds
        args = command[1:]
        if args[:3] == ("version", "--client", "-o"):
            return 0, json.dumps({"clientVersion": {"gitVersion": "v1.30.0"}}), ""
        if args == ("config", "current-context"):
            return 0, "kind-platform\n", ""
        if args[:3] == ("get", "namespace", "prod"):
            return 0, json.dumps({"metadata": {"name": "prod", "uid": "uid-1"}}), ""
        if args[:3] == ("auth", "can-i", "list"):
            return 0, "yes\n", ""
        return 1, "", f"unexpected command: {command}"

    monkeypatch.setattr("drift_engine.integrations.kubernetes.shutil.which", fake_which)
    monkeypatch.setattr(BaseCollector, "run_command", staticmethod(fake_run_command))

    result = await KubernetesIntegrationChecker().check(["prod"])

    assert result["ready"] is True
    assert result["context"] == "kind-platform"
    assert result["namespaces"] == ["prod"]
    assert {item["name"] for item in result["checks"]} == {
        "client_version",
        "current_context",
        "namespace:prod",
        "namespace:prod:read_workloads",
    }
