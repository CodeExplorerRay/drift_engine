# Production Deployment Guide

This guide describes a hardened production deployment for System Drift Engine.

## Required Controls

- Run with `DRIFT_ENVIRONMENT=production`.
- Keep `DRIFT_AUTH_REQUIRED=true`.
- Set `DRIFT_SERVICE_ACCOUNTS` to scoped service account JSON.
- Set `DRIFT_BASELINE_SIGNING_SECRET` to a strong random value.
- Set `DRIFT_AUTO_CREATE_SCHEMA=false` and run Alembic migrations before rollout.
- Keep `DRIFT_REMEDIATION_DRY_RUN=true` until runbooks are reviewed and approved.

Example service accounts:

```json
[
  {
    "id": "platform-ops",
    "key": "replace-with-secret",
    "scopes": [
      "baseline:write",
      "scan:execute",
      "policy:write",
      "jobs:write",
      "audit:read"
    ]
  },
  {
    "id": "remediation-approver",
    "key": "replace-with-another-secret",
    "scopes": [
      "remediation:plan",
      "remediation:approve",
      "remediation:execute",
      "audit:read"
    ]
  }
]
```

## Deployment

Local production-like compose:

```bash
export POSTGRES_PASSWORD="replace-me"
export DRIFT_BASELINE_SIGNING_SECRET="replace-me"
export DRIFT_SERVICE_ACCOUNTS='[{"id":"admin","key":"replace-me","scopes":["*"]}]'
docker compose -f docker-compose.prod.yml up -d
```

Managed platform deployment:

```bash
alembic -c alembic/alembic.ini upgrade head
uvicorn drift_engine.api.app:create_app --factory --host 0.0.0.0 --port 8080
```

## Health And Readiness

- `GET /health/live` verifies the process is alive.
- `GET /health/ready` verifies storage connectivity and schema availability.
- `GET /metrics` exposes Prometheus metrics when `DRIFT_METRICS_ENABLED=true`.
- `GET /audit` provides durable write and security event history for authorized callers.

## Scheduler

Enable persisted scheduled scans with:

```bash
DRIFT_SCHEDULER_ENABLED=true
DRIFT_SCHEDULER_INTERVAL_SECONDS=300
DRIFT_SCHEDULER_LOCK_TTL_SECONDS=300
```

Create scheduled jobs through `POST /jobs`. Multiple replicas are safe because job execution uses the `scheduler_locks` table before running a scan.

## Remediation

Recommended production flow:

1. `POST /remediation/reports/{report_id}/plan`
2. Review generated actions and runbook IDs.
3. `POST /remediation/actions/{action_id}/approve`
4. `POST /remediation/reports/{report_id}/execute` with `Idempotency-Key`.

Non-dry-run remediation requires an explicit approver identity. Raw shell commands are not accepted; execution is limited to named runbook templates.
