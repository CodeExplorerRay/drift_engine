# Production Deployment Guide

This guide describes a hardened production deployment for System Drift Engine.

## Required Controls

- Run with `DRIFT_ENVIRONMENT=production`.
- Keep `DRIFT_AUTH_REQUIRED=true`.
- Keep `DRIFT_ALLOW_DEV_AUTH=false`; the app rejects this flag outside local development.
- Set `DRIFT_CORS_ORIGINS` to the exact dashboard/API origins allowed to call the service.
- Set `DRIFT_SERVICE_ACCOUNTS` to scoped service account JSON.
- Set `DRIFT_BASELINE_SIGNING_SECRET` to a strong random value.
- Set `DRIFT_AUTO_CREATE_SCHEMA=false` and run Alembic migrations before rollout.
- Keep `DRIFT_REMEDIATION_DRY_RUN=true` until runbooks are reviewed and approved.
- Keep `DRIFT_METRICS_PUBLIC=false` unless metrics are protected by network policy.

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

Cloud VM deployment:

1. Provision a Linux VM with Docker Engine, Docker Compose, firewall rules, and encrypted disk storage.
2. Restrict inbound access to the dashboard/API port through a VPN, private subnet, reverse proxy, or allowlist.
3. Store `POSTGRES_PASSWORD`, `DRIFT_BASELINE_SIGNING_SECRET`, and `DRIFT_SERVICE_ACCOUNTS` in the host secret manager or an environment file that is not committed.
4. Run migrations before the app rollout:

```bash
alembic -c alembic/alembic.ini upgrade head
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Kubernetes deployment guidance:

1. Use a dedicated namespace such as `drift-engine`.
2. Store app secrets in Kubernetes `Secret` objects or an external secrets operator.
3. Run Postgres as a managed service where possible. If running in-cluster, use persistent volumes, backups, and anti-affinity.
4. Run Alembic migrations as a one-shot `Job` before updating the API `Deployment`.
5. Expose the API behind an internal ingress, private load balancer, or authenticated gateway.
6. Use a restricted `ServiceAccount` for Kubernetes collection. Grant read-only verbs for namespaces, workloads, services, ingresses, configmaps, service accounts, roles, bindings, and pods.

Single-process managed platform deployment:

```bash
alembic -c alembic/alembic.ini upgrade head
uvicorn drift_engine.api.app:create_app --factory --host 0.0.0.0 --port 8080
```

## Health And Readiness

- `GET /health/live` verifies the process is alive.
- `GET /health/ready` verifies storage connectivity and schema availability.
- `GET /metrics` exposes Prometheus metrics when `DRIFT_METRICS_ENABLED=true`, but requests are still authenticated and restricted to localhost or private/internal networks unless `DRIFT_METRICS_PUBLIC=true`.
- `GET /audit` provides durable write and security event history for authorized callers.

## Backups

Back up Postgres before every deployment and on a fixed schedule:

```bash
pg_dump --format=custom --file drift-$(date +%Y%m%d%H%M%S).dump "$DATABASE_URL"
```

Minimum tables to protect are baselines, snapshots, drift reports, policies, audit events, scheduled jobs, job runs, remediation plans, remediation actions, remediation executions, and scheduler locks. Store backups in encrypted object storage with lifecycle retention and test restore into a non-production database regularly.

Restore example:

```bash
createdb drift_restore
pg_restore --dbname drift_restore drift-20260101000000.dump
```

## Monitoring

Scrape `GET /metrics` with Prometheus or a compatible collector. Alert on:

- Readiness failure from `GET /health/ready`.
- Sustained API 5xx responses.
- Scheduler jobs failing or not running on time.
- Critical drift findings.
- Remediation actions in `failed` status.
- Postgres storage, connection, and replication issues.

Forward structured logs to your logging platform and preserve correlation IDs for incident review. Use `GET /audit` for write-path accountability, but keep audit data immutable in the database.

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

1. Confirm capability with `GET /remediation/capability`.
1. `POST /remediation/reports/{report_id}/plan`
2. Review generated actions and runbook IDs.
3. `POST /remediation/actions/{action_id}/approve`
4. `POST /remediation/reports/{report_id}/execute` with `Idempotency-Key`.

Non-dry-run remediation requires an explicit approver identity and a real executor. If the backend is using the noop executor, execution responses are simulation-only and skipped. Raw shell commands are not accepted; real execution must be limited to named runbook templates.
