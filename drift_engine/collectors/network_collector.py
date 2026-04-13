from __future__ import annotations

import socket
from typing import Any

from drift_engine.collectors.base import BaseCollector, CollectionContext, CollectorConfig
from drift_engine.core.models import StateSnapshot


class NetworkCollector(BaseCollector):
    resource_type = "network"

    def __init__(self, config: CollectorConfig | None = None) -> None:
        super().__init__("network", config)

    async def collect(self, context: CollectionContext) -> StateSnapshot:
        hostname = socket.gethostname()
        fqdn = socket.getfqdn()
        addresses = self._resolve_addresses(hostname)
        resources: dict[str, dict[str, Any]] = {
            self.resource_key("identity"): {
                "resource_type": self.resource_type,
                "hostname": hostname,
                "fqdn": fqdn,
                "addresses": addresses,
            }
        }
        resources.update(await self._collect_listeners())
        return StateSnapshot(source=self.name, resources=resources)

    @staticmethod
    def _resolve_addresses(hostname: str) -> list[str]:
        try:
            infos = socket.getaddrinfo(hostname, None)
        except socket.gaierror:
            return []
        return sorted({info[4][0] for info in infos})

    async def _collect_listeners(self) -> dict[str, dict[str, Any]]:
        commands = [
            ("ss", "-tuln"),
            ("netstat", "-ano"),
        ]
        for command in commands:
            try:
                code, stdout, _ = await self.run_command(*command, timeout_seconds=5.0)
            except (FileNotFoundError, TimeoutError):
                continue
            if code == 0:
                return self._parse_listeners(command[0], stdout)
        return {}

    def _parse_listeners(self, command: str, stdout: str) -> dict[str, dict[str, Any]]:
        listeners: dict[str, dict[str, Any]] = {}
        for line in stdout.splitlines():
            parts = line.split()
            if not parts or parts[0].lower() in {"netid", "proto", "active"}:
                continue
            item = (
                self._parse_ss_line(parts)
                if command == "ss"
                else self._parse_netstat_line(parts)
            )
            if item is None:
                continue
            local_address = str(item["local_address"])
            key = self.resource_key(f"listener/{item['protocol']}/{local_address}")
            listeners[key] = {
                "resource_type": self.resource_type,
                "kind": "listener",
                "source_command": command,
                **item,
            }
        return listeners

    @staticmethod
    def _parse_ss_line(parts: list[str]) -> dict[str, Any] | None:
        if len(parts) < 5:
            return None
        return {
            "protocol": parts[0].lower(),
            "state": parts[1],
            "local_address": parts[4],
            "peer_address": parts[5] if len(parts) > 5 else "",
            "pid": None,
        }

    @staticmethod
    def _parse_netstat_line(parts: list[str]) -> dict[str, Any] | None:
        protocol = parts[0].lower()
        if protocol == "tcp" and len(parts) >= 5:
            return {
                "protocol": protocol,
                "state": parts[3],
                "local_address": parts[1],
                "peer_address": parts[2],
                "pid": parts[4],
            }
        if protocol == "udp" and len(parts) >= 4:
            return {
                "protocol": protocol,
                "state": "",
                "local_address": parts[1],
                "peer_address": parts[2],
                "pid": parts[3],
            }
        return None
