# Rollback Procedures

Use this runbook when a deployment, migration, scheduled scan, or remediation action causes unexpected behavior.

## Application Rollback

1. Stop new writes by disabling schedulers:

```bash
DRIFT_SCHEDULER_ENABLED=false
```

2. Roll back the application image to the previous known-good tag:

```bash
docker compose -f docker-compose.prod.yml pull api
docker compose -f docker-compose.prod.yml up -d api
```

3. Verify:

```bash
curl -fsS http://127.0.0.1:8080/health/live
curl -fsS http://127.0.0.1:8080/health/ready
```

## Migration Rollback

Prefer forward-fix migrations for production data. If rollback is required and approved:

```bash
alembic -c alembic/alembic.ini downgrade -1
```

Before downgrading, export the affected tables:

```bash
pg_dump --data-only --table audit_events --table scheduled_jobs --table job_runs drift > drift-operational-backup.sql
```

## Remediation Rollback

Remediation actions are intentionally gated and runbook based. If a runbook action causes impact:

1. Disable execution by setting `DRIFT_REMEDIATION_ENABLED=false`.
2. Query `/remediation/actions` and `/audit` for the action ID, approver, runbook ID, and idempotency key.
3. Execute the corresponding manual rollback runbook owned by the operations team.
4. Keep the original audit events immutable; add a follow-up incident note externally rather than editing action history.

## Scheduler Rollback

Disable a problematic scheduled scan by setting the job `enabled` field to false through the database or by redeploying with `DRIFT_SCHEDULER_ENABLED=false` while an API update endpoint is unavailable.

Operational SQL fallback:

```sql
UPDATE scheduled_jobs
SET enabled = false,
    document = jsonb_set(document, '{enabled}', 'false'::jsonb),
    updated_at = now()
WHERE id = '<job-id>';
```
