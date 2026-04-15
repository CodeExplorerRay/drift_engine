from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Literal

from pydantic import AnyHttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings use the DRIFT_ prefix so deployment platforms can safely
    co-locate this service with other workloads.
    """

    model_config = SettingsConfigDict(
        env_prefix="DRIFT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["local", "test", "staging", "production"] = "local"
    service_name: str = "system-drift-engine"
    log_level: str = "INFO"
    # Containerized services intentionally bind all interfaces.
    host: str = "0.0.0.0"  # noqa: S104  # nosec B104
    port: int = 8080

    storage_backend: Literal["auto", "memory", "postgres"] = "auto"
    database_url: str = "sqlite+aiosqlite:///./drift_engine.db"
    auto_create_schema: bool = False
    redis_url: str | None = None
    elasticsearch_url: str | None = None

    api_keys: SecretStr | None = None
    service_accounts: SecretStr | None = None
    auth_required: bool = True
    allow_dev_auth: bool = False
    rate_limit_per_minute: int = 600
    cors_origins: str = ""

    baseline_signing_secret: SecretStr | None = None
    collector_timeout_seconds: float = 30.0
    max_collector_concurrency: int = 8
    scheduler_enabled: bool = False
    scheduler_interval_seconds: int = 300
    scheduler_lock_ttl_seconds: int = 300
    scheduler_owner_id: str = "api"

    enabled_integrations: str = ""
    kubernetes_namespaces: str = ""
    aws_regions: str = "us-east-1"
    aws_collect_s3_buckets: bool = True
    azure_subscription_id: str | None = None

    remediation_enabled: bool = False
    remediation_auto_approve_below_risk: float = 20.0
    remediation_dry_run: bool = True

    otel_exporter_otlp_endpoint: AnyHttpUrl | None = None
    metrics_enabled: bool = True
    metrics_public: bool = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_strict_environment(self) -> bool:
        return self.environment in {"staging", "production"}

    @property
    def local_dev_auth_enabled(self) -> bool:
        return self.environment == "local" and self.allow_dev_auth

    @property
    def cors_origin_values(self) -> list[str]:
        return self._csv_values(self.cors_origins)

    @property
    def api_key_values(self) -> list[str]:
        if self.api_keys is None:
            return []
        raw = self.api_keys.get_secret_value()
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def service_account_values(self) -> list[dict[str, Any]]:
        accounts: list[dict[str, Any]] = []
        if self.service_accounts is not None:
            raw = self.service_accounts.get_secret_value().strip()
            if raw:
                payload = json.loads(raw)
                records = payload.get("accounts", []) if isinstance(payload, dict) else payload
                if not isinstance(records, list):
                    raise ValueError("DRIFT_SERVICE_ACCOUNTS must be a JSON list or object")
                for index, item in enumerate(records, start=1):
                    if not isinstance(item, dict):
                        raise ValueError("DRIFT_SERVICE_ACCOUNTS entries must be objects")
                    key = str(item.get("key", "")).strip()
                    if not key:
                        continue
                    raw_scopes = item.get("scopes", [])
                    scopes = raw_scopes if isinstance(raw_scopes, list) else [str(raw_scopes)]
                    accounts.append(
                        {
                            "id": str(item.get("id") or f"service-account-{index}"),
                            "key": key,
                            "scopes": [str(scope) for scope in scopes],
                            "actor_type": str(item.get("actor_type") or "service_account"),
                        }
                    )
        for index, key in enumerate(self.api_key_values, start=1):
            accounts.append(
                {
                    "id": f"legacy-api-key-{index}",
                    "key": key,
                    "scopes": ["*"],
                    "actor_type": "api_key",
                }
            )
        return accounts

    @property
    def resolved_storage_backend(self) -> Literal["memory", "postgres"]:
        if self.storage_backend != "auto":
            return self.storage_backend
        if self.database_url.startswith(("postgresql://", "postgresql+asyncpg://")):
            return "postgres"
        return "memory"

    @property
    def enabled_integration_names(self) -> set[str]:
        return {item.lower() for item in self._csv_values(self.enabled_integrations)}

    @property
    def kubernetes_namespace_values(self) -> list[str]:
        return self._csv_values(self.kubernetes_namespaces)

    @property
    def aws_region_values(self) -> list[str]:
        return self._csv_values(self.aws_regions) or ["us-east-1"]

    @staticmethod
    def _csv_values(raw: str | None) -> list[str]:
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    def validate_runtime_security(self) -> None:
        if self.allow_dev_auth and self.environment != "local":
            raise ValueError(
                "DRIFT_ALLOW_DEV_AUTH=true is only allowed when DRIFT_ENVIRONMENT=local"
            )
        if not self.is_strict_environment:
            return
        if not self.auth_required:
            raise ValueError("DRIFT_AUTH_REQUIRED=false is not allowed in staging or production")
        if not self.service_account_values:
            raise ValueError(
                "DRIFT_SERVICE_ACCOUNTS or DRIFT_API_KEYS is required in staging and production"
            )
        if self.baseline_signing_secret is None:
            raise ValueError(
                "DRIFT_BASELINE_SIGNING_SECRET is required in staging and production"
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
