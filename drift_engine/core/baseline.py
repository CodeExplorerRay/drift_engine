from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from drift_engine.core.exceptions import BaselineValidationError
from drift_engine.core.models import Baseline, StateSnapshot
from drift_engine.utils.crypto import sign_payload, verify_signature
from drift_engine.utils.serialization import canonical_hash


class BaselineManager:
    """Creates, validates, signs, and verifies immutable desired-state baselines."""

    def __init__(self, signing_secret: str | None = None) -> None:
        self.signing_secret = signing_secret

    def create(
        self,
        *,
        name: str,
        resources: Mapping[str, Mapping[str, Any]],
        version: str = "1.0.0",
        scope: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Baseline:
        normalized = self.normalize_resources(resources)
        baseline = Baseline(
            name=name,
            version=version,
            resources=normalized,
            scope=scope or {},
            metadata=metadata or {},
        )
        self.validate(baseline)
        if self.signing_secret:
            baseline.signature = sign_payload(baseline.unsigned_document(), self.signing_secret)
        return baseline

    def from_snapshot(
        self,
        *,
        name: str,
        snapshot: StateSnapshot,
        version: str = "1.0.0",
        metadata: dict[str, Any] | None = None,
    ) -> Baseline:
        return self.create(
            name=name,
            resources=snapshot.resources,
            version=version,
            scope={"source": snapshot.source},
            metadata={"snapshot_id": snapshot.id, **(metadata or {})},
        )

    def validate(self, baseline: Baseline) -> None:
        if not baseline.name.strip():
            raise BaselineValidationError("baseline name is required")
        if not baseline.resources:
            raise BaselineValidationError("baseline must contain at least one resource")
        for key, resource in baseline.resources.items():
            if not key.strip():
                raise BaselineValidationError("baseline resource keys must be non-empty")
            if not isinstance(resource, dict):
                raise BaselineValidationError(f"resource {key!r} must be a mapping")

        expected_checksum = canonical_hash(baseline.content_document())
        if baseline.checksum != expected_checksum:
            raise BaselineValidationError("baseline checksum does not match content")

    def verify(self, baseline: Baseline) -> None:
        self.validate(baseline)
        if self.signing_secret:
            if not baseline.signature:
                raise BaselineValidationError("signed baseline is missing a signature")
            if not verify_signature(
                baseline.unsigned_document(), baseline.signature, self.signing_secret
            ):
                raise BaselineValidationError("baseline signature verification failed")

    @staticmethod
    def normalize_resources(
        resources: Mapping[str, Mapping[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        normalized: dict[str, dict[str, Any]] = {}
        for key, value in resources.items():
            normalized[key.strip()] = dict(sorted(dict(value).items()))
        return dict(sorted(normalized.items()))
