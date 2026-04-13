from __future__ import annotations

import dataclasses
import datetime as dt
import enum
import hashlib
import json
from decimal import Decimal
from typing import Any, cast


class CanonicalJSONEncoder(json.JSONEncoder):
    """JSON encoder that makes domain objects deterministic and serializable."""

    def default(self, obj: Any) -> Any:
        if hasattr(obj, "__dataclass_fields__") and not isinstance(obj, type):
            return dataclasses.asdict(cast(Any, obj))
        if isinstance(obj, enum.Enum):
            return obj.value
        if isinstance(obj, dt.datetime | dt.date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, set):
            return sorted(obj)
        return super().default(obj)


def canonical_dumps(value: Any) -> str:
    return json.dumps(
        value,
        cls=CanonicalJSONEncoder,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def canonical_hash(value: Any, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    digest.update(canonical_dumps(value).encode("utf-8"))
    return digest.hexdigest()


def redact(value: Any, sensitive_keys: set[str] | None = None) -> Any:
    sensitive = sensitive_keys or {"password", "secret", "token", "key", "credential"}
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if any(part in key.lower() for part in sensitive):
                redacted[key] = "***REDACTED***"
            else:
                redacted[key] = redact(item, sensitive)
        return redacted
    if isinstance(value, list):
        return [redact(item, sensitive) for item in value]
    return value


def deep_get(value: dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current
