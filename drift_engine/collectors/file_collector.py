from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from typing import Any

from drift_engine.collectors.base import BaseCollector, CollectionContext, CollectorConfig
from drift_engine.core.models import StateSnapshot


class FileCollector(BaseCollector):
    resource_type = "file"

    def __init__(self, config: CollectorConfig | None = None) -> None:
        super().__init__("file", config)

    async def collect(self, context: CollectionContext) -> StateSnapshot:
        paths = context.scope.get("file_paths") or self.config.settings.get("paths") or []
        include_mtime = bool(
            context.scope.get(
                "include_file_mtime",
                self.config.settings.get("include_mtime", False),
            )
        )
        resources: dict[str, dict[str, Any]] = {}
        errors: list[str] = []

        for raw_path in paths:
            path = Path(str(raw_path)).expanduser()
            try:
                if not path.exists():
                    resources[self.resource_key(str(path))] = {
                        "resource_type": self.resource_type,
                        "path": str(path),
                        "exists": False,
                    }
                    continue
                resources[self.resource_key(str(path))] = self._inspect(
                    path,
                    include_mtime=include_mtime,
                )
            except OSError as error:
                errors.append(f"{path}: {error}")

        return StateSnapshot(
            source=self.name,
            resources=resources,
            metadata={"errors": errors, "path_count": len(paths)},
        )

    def _inspect(self, path: Path, *, include_mtime: bool = False) -> dict[str, Any]:
        stat_result = path.stat()
        document: dict[str, Any] = {
            "resource_type": self.resource_type,
            "path": str(path),
            "exists": True,
            "mode": stat.filemode(stat_result.st_mode),
            "permissions": oct(stat.S_IMODE(stat_result.st_mode)),
            "size": stat_result.st_size,
            "owner_uid": getattr(stat_result, "st_uid", None),
            "group_gid": getattr(stat_result, "st_gid", None),
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
        }
        if include_mtime:
            document["mtime_ns"] = stat_result.st_mtime_ns
        if path.is_file():
            document["sha256"] = self._hash_file(path)
        return document

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()


def default_file_paths() -> list[str]:
    candidates = [
        "/etc/passwd",
        "/etc/group",
        "/etc/ssh/sshd_config",
        "C:/Windows/System32/drivers/etc/hosts",
    ]
    return [path for path in candidates if os.path.exists(path)]
