from __future__ import annotations

from typing import Any

from drift_engine.core.models import Baseline, StateSnapshot


def baseline_factory(resources: dict[str, dict[str, Any]] | None = None) -> Baseline:
    return Baseline(
        name="golden-linux",
        resources=resources
        or {
            "local::_::_::package::openssl": {
                "resource_type": "package",
                "name": "openssl",
                "version": "3.0.0",
            }
        },
    )


def snapshot_factory(resources: dict[str, dict[str, Any]] | None = None) -> StateSnapshot:
    return StateSnapshot(
        source="test",
        resources=resources
        or {
            "local::_::_::package::openssl": {
                "resource_type": "package",
                "name": "openssl",
                "version": "3.0.1",
            }
        },
    )
