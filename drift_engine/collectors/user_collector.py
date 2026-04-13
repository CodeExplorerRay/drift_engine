from __future__ import annotations

import getpass
import os
import platform

from drift_engine.collectors.base import BaseCollector, CollectionContext, CollectorConfig
from drift_engine.core.models import StateSnapshot


class UserCollector(BaseCollector):
    resource_type = "user"

    def __init__(self, config: CollectorConfig | None = None) -> None:
        super().__init__("user", config)

    async def collect(self, context: CollectionContext) -> StateSnapshot:
        if platform.system().lower() != "windows":
            return self._collect_posix()
        return StateSnapshot(
            source=self.name,
            resources={
                self.resource_key(getpass.getuser()): {
                    "resource_type": self.resource_type,
                    "username": getpass.getuser(),
                    "userprofile": os.environ.get("USERPROFILE"),
                    "groups": [],
                }
            },
        )

    def _collect_posix(self) -> StateSnapshot:
        import grp
        import pwd

        resources: dict[str, dict[str, object]] = {}
        for entry in pwd.getpwall():  # type: ignore[attr-defined]
            groups = [
                group.gr_name
                for group in grp.getgrall()  # type: ignore[attr-defined]
                if entry.pw_name in group.gr_mem
            ]
            resources[self.resource_key(entry.pw_name)] = {
                "resource_type": self.resource_type,
                "username": entry.pw_name,
                "uid": entry.pw_uid,
                "gid": entry.pw_gid,
                "home": entry.pw_dir,
                "shell": entry.pw_shell,
                "groups": sorted(groups),
            }
        return StateSnapshot(source=self.name, resources=resources)
