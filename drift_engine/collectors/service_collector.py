from __future__ import annotations

import json
import platform
from typing import Any

from drift_engine.collectors.base import BaseCollector, CollectionContext, CollectorConfig
from drift_engine.core.models import StateSnapshot


class ServiceCollector(BaseCollector):
    resource_type = "service"

    def __init__(self, config: CollectorConfig | None = None) -> None:
        super().__init__("service", config)

    async def collect(self, context: CollectionContext) -> StateSnapshot:
        system = platform.system().lower()
        if system == "linux":
            return await self._collect_systemd()
        if system == "windows":
            return await self._collect_windows_services()
        return StateSnapshot(
            source=self.name,
            resources={
                self.resource_key("service-inspection"): {
                    "resource_type": self.resource_type,
                    "platform": system,
                    "supported": False,
                }
            },
        )

    async def _collect_systemd(self) -> StateSnapshot:
        code, stdout, stderr = await self.run_command(
            "systemctl",
            "list-units",
            "--type=service",
            "--all",
            "--no-legend",
            "--no-pager",
            timeout_seconds=self.config.timeout_seconds,
        )
        resources: dict[str, dict[str, object]] = {}
        if code == 0:
            for line in stdout.splitlines():
                parts = line.split(None, 4)
                if len(parts) >= 4:
                    name, load, active, sub = parts[:4]
                    resources[self.resource_key(name)] = {
                        "resource_type": self.resource_type,
                        "name": name,
                        "load": load,
                        "active": active,
                        "sub": sub,
                    }
        return StateSnapshot(source=self.name, resources=resources, metadata={"stderr": stderr})

    async def _collect_windows_services(self) -> StateSnapshot:
        code, stdout, stderr = await self.run_command(
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-Service | Select-Object Name,Status,StartType | ConvertTo-Json",
            timeout_seconds=self.config.timeout_seconds,
        )
        if code == 0:
            return StateSnapshot(
                source=self.name,
                resources=self._parse_windows_services(stdout),
                metadata={"stderr": stderr},
            )
        return StateSnapshot(
            source=self.name,
            resources={},
            metadata={"inspection_error": stderr, "exit_code": code},
        )

    def _parse_windows_services(self, stdout: str) -> dict[str, dict[str, Any]]:
        payload = json.loads(stdout or "[]")
        records = payload if isinstance(payload, list) else [payload]
        resources: dict[str, dict[str, Any]] = {}
        for item in records:
            if not isinstance(item, dict):
                continue
            name = str(item.get("Name") or "unknown")
            resources[self.resource_key(name)] = {
                "resource_type": self.resource_type,
                "name": name,
                "status": item.get("Status"),
                "start_type": item.get("StartType"),
                "platform": "windows",
            }
        return resources
