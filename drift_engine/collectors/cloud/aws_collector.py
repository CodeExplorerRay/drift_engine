from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from drift_engine.collectors.base import BaseCollector, CollectionContext, CollectorConfig
from drift_engine.core.models import StateSnapshot


class AWSCollector(BaseCollector):
    resource_type = "aws"

    def __init__(self, config: CollectorConfig | None = None) -> None:
        super().__init__("aws", config)

    async def collect(self, context: CollectionContext) -> StateSnapshot:
        try:
            import boto3
        except ImportError:
            return StateSnapshot(
                source=self.name,
                resources={},
                metadata={"enabled": False, "reason": "boto3 is not installed"},
            )

        regions = (
            context.scope.get("aws_regions") or self.config.settings.get("regions") or ["us-east-1"]
        )
        resources: dict[str, dict[str, Any]] = {}
        errors: list[str] = []
        for region in regions:
            try:
                ec2 = boto3.client("ec2", region_name=region)
                resources.update(
                    self._collect_security_groups(
                        ec2=ec2,
                        account_id=context.scope.get("aws_account_id"),
                        region=str(region),
                    )
                )
                if self.config.settings.get("collect_s3_buckets", True):
                    s3 = boto3.client("s3", region_name=region)
                    resources.update(
                        self._collect_s3_buckets(
                            s3=s3,
                            account_id=context.scope.get("aws_account_id"),
                        )
                    )
            except Exception as error:
                errors.append(f"{region}: {error}")
        return StateSnapshot(source=self.name, resources=resources, metadata={"errors": errors})

    def _collect_security_groups(
        self,
        *,
        ec2: Any,
        account_id: object,
        region: str,
    ) -> dict[str, dict[str, Any]]:
        resources: dict[str, dict[str, Any]] = {}
        paginator = ec2.get_paginator("describe_security_groups")
        for page in self._with_retries(lambda: paginator.paginate()):
            for group in page.get("SecurityGroups", []):
                group_id = group["GroupId"]
                account = str(account_id) if account_id is not None else None
                resources[
                    self.resource_key(
                        f"security-group/{group_id}",
                        provider="aws",
                        account=account,
                        region=region,
                    )
                ] = self._security_group_to_resource(group, region=region)
        return resources

    def _collect_s3_buckets(self, *, s3: Any, account_id: object) -> dict[str, dict[str, Any]]:
        resources: dict[str, dict[str, Any]] = {}
        response = self._with_retries(s3.list_buckets)
        for bucket in response.get("Buckets", []):
            name = bucket.get("Name", "unknown")
            account = str(account_id) if account_id is not None else None
            resources[
                self.resource_key(
                    f"s3-bucket/{name}",
                    provider="aws",
                    account=account,
                    region="global",
                )
            ] = {
                "resource_type": "s3_bucket",
                "provider": "aws",
                "name": name,
                "creation_date": str(bucket.get("CreationDate")),
            }
        return resources

    @staticmethod
    def _security_group_to_resource(group: dict[str, Any], *, region: str) -> dict[str, Any]:
        return {
            "resource_type": "security_group",
            "provider": "aws",
            "region": region,
            "group_id": group["GroupId"],
            "name": group.get("GroupName"),
            "description": group.get("Description"),
            "vpc_id": group.get("VpcId"),
            "ingress": group.get("IpPermissions", []),
            "egress": group.get("IpPermissionsEgress", []),
            "tags": group.get("Tags", []),
        }

    @staticmethod
    def _with_retries(operation: Callable[[], Any], *, attempts: int = 3) -> Any:
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return operation()
            except Exception as error:
                last_error = error
                if attempt + 1 == attempts:
                    break
                time.sleep(0.2 * (2**attempt))
        raise RuntimeError("AWS collector operation failed") from last_error
