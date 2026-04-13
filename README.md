# System Drift Engine

System Drift Engine continuously collects infrastructure state, compares it to signed baselines, evaluates policy, scores operational and security risk, emits events, and can execute gated remediation.

## Quick Start

```bash
pip install -e ".[dev]"
drift-engine serve --reload
```

Open the browser dashboard at `http://127.0.0.1:8080/`.

The API console is still available at `http://127.0.0.1:8080/docs`. In production, use scoped `DRIFT_SERVICE_ACCOUNTS`, a strong `DRIFT_BASELINE_SIGNING_SECRET`, durable Postgres storage, and explicit Alembic migrations.

## Docker

```bash
docker compose up --build -d
docker compose ps
```

Useful local links:

- Dashboard: `http://127.0.0.1:8080/`
- API docs: `http://127.0.0.1:8080/docs`
- Liveness: `http://127.0.0.1:8080/health/live`
- Readiness: `http://127.0.0.1:8080/health/ready`

The Docker profile uses `DRIFT_STORAGE_BACKEND=postgres` and stores baselines, snapshots, drift reports, and custom policies in Postgres. `DRIFT_AUTO_CREATE_SCHEMA=true` is enabled for local Docker convenience; production deployments should run Alembic migrations explicitly instead.

For production-like settings, use `docker-compose.prod.yml` and read [Production Deployment Guide](docs/production.md). Rollback procedures are documented in [Rollback Procedures](docs/rollback.md).

## Integrations

Local collectors are enabled by default. External integrations are opt-in so the engine does not accidentally scan a cluster or cloud account before operators configure credentials and scope.

Enable integrations with `DRIFT_ENABLED_INTEGRATIONS`:

```bash
DRIFT_ENABLED_INTEGRATIONS=kubernetes,aws,azure
```

Supported integrations:

- Kubernetes: uses `kubectl` and the active kubeconfig context. Optional scope: `DRIFT_KUBERNETES_NAMESPACES=prod,platform`.
- AWS: install `system-drift-engine[aws]`, provide credentials through the standard AWS provider chain, and set `DRIFT_AWS_REGIONS=us-east-1,us-west-2`.
- Azure: install `system-drift-engine[azure]`, authenticate with `DefaultAzureCredential`, and set `DRIFT_AZURE_SUBSCRIPTION_ID=<subscription-id>`.

The dashboard shows integration readiness, and the API exposes the same information at `GET /integrations`.

### Kubernetes Quick Demo

Use this path when you want to see real drift instead of static sample data.

```bash
kubectl apply -f examples/kubernetes/baseline.yaml
```

Start the engine with Kubernetes enabled:

```bash
DRIFT_ENABLED_INTEGRATIONS=kubernetes
DRIFT_KUBERNETES_NAMESPACES=drift-demo
drift-engine serve --reload
```

Then open `http://127.0.0.1:8080/`, enter `drift-demo` in Kubernetes namespaces, click **Check Kubernetes integration**, select the Kubernetes collector, and capture a baseline.

Create drift:

```bash
kubectl apply -f examples/kubernetes/drift.yaml
```

Run a drift scan in the dashboard. Expected findings include changed replicas, changed container image/security context, and public `LoadBalancer` exposure.

## Architecture

The engine is intentionally modular:

- Collectors gather state from host, Kubernetes, AWS, Azure, and custom sources.
- Baselines define desired state and can be signed to detect tampering.
- The drift detector produces stable fingerprints for added, removed, and modified resources.
- The policy engine maps drift to compliance violations and risk.
- Remediation plans are generated separately from execution and can require approval.
- Scheduled scan jobs, audit events, and remediation approvals are durable and API-visible.
- Storage adapters support in-memory testing, Postgres, Redis, and Elasticsearch.
- Events, metrics, traces, correlation IDs, and structured logging are first-class.

## API Security

Production service accounts are JSON records with explicit scopes. Use `X-API-Key` to authenticate API calls.

```json
[{"id":"platform-ops","key":"replace-me","scopes":["baseline:write","scan:execute","jobs:write","audit:read"]}]
```

Available write scopes include `baseline:write`, `scan:execute`, `policy:write`, `jobs:write`, `remediation:plan`, `remediation:approve`, `remediation:execute`, and `audit:read`.
