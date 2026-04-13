from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from typing import Any

from drift_engine.collectors.base import BaseCollector


@dataclass(slots=True)
class IntegrationCheck:
    name: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.status == "passed"

    def to_document(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "details": self.details,
            "error": self.error,
        }


class KubernetesIntegrationChecker:
    """Runs non-mutating checks against the operator's active kubectl context."""

    def __init__(self, *, timeout_seconds: float = 8.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def check(self, namespaces: list[str] | None = None) -> dict[str, Any]:
        checks: list[IntegrationCheck] = []
        if shutil.which("kubectl") is None:
            checks.append(
                IntegrationCheck(
                    name="kubectl",
                    status="failed",
                    error="kubectl was not found on PATH",
                )
            )
            return self._document(checks=checks, context=None, namespaces=namespaces or [])

        version = await self._kubectl_json("client_version", "version", "--client", "-o", "json")
        checks.append(version)

        context = await self._kubectl_text("current_context", "config", "current-context")
        checks.append(context)

        namespace_values = namespaces or []
        if namespace_values:
            for namespace in namespace_values:
                checks.append(
                    await self._kubectl_json(
                        f"namespace:{namespace}",
                        "get",
                        "namespace",
                        namespace,
                        "-o",
                        "json",
                    )
                )
                checks.append(
                    await self._kubectl_text(
                        f"namespace:{namespace}:read_workloads",
                        "auth",
                        "can-i",
                        "list",
                        "deployments",
                        "--namespace",
                        namespace,
                    )
                )
        else:
            checks.append(
                await self._kubectl_text(
                    "cluster:list_namespaces",
                    "auth",
                    "can-i",
                    "list",
                    "namespaces",
                )
            )
            checks.append(
                await self._kubectl_text(
                    "cluster:list_workloads",
                    "auth",
                    "can-i",
                    "list",
                    "deployments",
                    "--all-namespaces",
                )
            )

        return self._document(
            checks=checks,
            context=context.details.get("value") if context.passed else None,
            namespaces=namespace_values,
        )

    def _document(
        self,
        *,
        checks: list[IntegrationCheck],
        context: str | None,
        namespaces: list[str],
    ) -> dict[str, Any]:
        ready = all(check.passed for check in checks)
        return {
            "integration": "kubernetes",
            "ready": ready,
            "context": context,
            "namespaces": namespaces,
            "checks": [check.to_document() for check in checks],
        }

    async def _kubectl_json(self, name: str, *args: str) -> IntegrationCheck:
        code, stdout, stderr = await BaseCollector.run_command(
            "kubectl",
            *args,
            timeout_seconds=self.timeout_seconds,
        )
        if code != 0:
            return IntegrationCheck(name=name, status="failed", error=stderr.strip())
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            payload = {"raw": stdout.strip()}
        return IntegrationCheck(name=name, status="passed", details=self._summarize(payload))

    async def _kubectl_text(self, name: str, *args: str) -> IntegrationCheck:
        code, stdout, stderr = await BaseCollector.run_command(
            "kubectl",
            *args,
            timeout_seconds=self.timeout_seconds,
        )
        value = stdout.strip()
        if code != 0:
            return IntegrationCheck(
                name=name,
                status="failed",
                details={"value": value},
                error=stderr.strip(),
            )
        if value.lower() == "no":
            return IntegrationCheck(
                name=name,
                status="failed",
                details={"value": value},
                error="permission denied",
            )
        return IntegrationCheck(name=name, status="passed", details={"value": value})

    @staticmethod
    def _summarize(payload: dict[str, Any]) -> dict[str, Any]:
        client_version = payload.get("clientVersion")
        metadata = payload.get("metadata")
        if isinstance(client_version, dict):
            return {"git_version": client_version.get("gitVersion")}
        if isinstance(metadata, dict):
            return {"name": metadata.get("name"), "uid": metadata.get("uid")}
        return payload
