# System Drift Engine

System Drift Engine continuously collects infrastructure state, compares it to signed baselines, evaluates policy, scores operational and security risk, emits events, and plans gated remediation.

## Quick Start

```bash
cp .env.example .env
pip install -e ".[dev]"
cd frontend
npm install
npm run build
cd ..
drift-engine serve --reload
```

Open the browser dashboard at `http://localhost:8080/`.

The API console is still available at `http://localhost:8080/docs`. In production, use scoped `DRIFT_SERVICE_ACCOUNTS`, a strong `DRIFT_BASELINE_SIGNING_SECRET`, durable Postgres storage, and explicit Alembic migrations.

For Windows PowerShell, use this instead of `cp`:

```powershell
Copy-Item .env.example .env
```

The local `.env` file is ignored by git. It is for development-only defaults such as `local-dev-key`, local ports, and optional integration toggles.
Local auth fallback is only enabled when `DRIFT_ALLOW_DEV_AUTH=true`; staging and production refuse startup without configured API keys or service accounts. Local remediation uses the noop executor in dry-run/simulation mode, so the dashboard workflow can be tested without changing the host. Keep non-dry-run remediation disabled until a real runbook executor is configured and reviewed.

## Docker

```bash
docker compose up --build -d
docker compose ps
```

Useful local links:

- Dashboard: `http://localhost:8080/`
- API docs: `http://localhost:8080/docs`
- Liveness: `http://localhost:8080/health/live`
- Readiness: `http://localhost:8080/health/ready`
- Metrics: `http://localhost:8080/metrics` from localhost/internal networks only unless explicitly exposed

The Docker profile uses `DRIFT_STORAGE_BACKEND=postgres` and stores baselines, snapshots, drift reports, and custom policies in Postgres. `DRIFT_AUTO_CREATE_SCHEMA=true` is enabled for local Docker convenience; production deployments should run Alembic migrations explicitly instead.

For production-like settings, use `docker-compose.prod.yml` and read [Production Deployment Guide](docs/production.md). Rollback procedures are documented in [Rollback Procedures](docs/rollback.md).

## Self-Hosted CI/CD

The repo includes a no-billing Woodpecker CI setup for running checks on your own Docker host:

```bash
docker compose -f docker-compose.ci.yml up -d
```

Open the CI web UI at `http://localhost:8000`. The pipeline in `.woodpecker.yml` runs linting, type checks, tests with coverage, Alembic migration validation, an API dashboard smoke test, and a dry-run Docker image build. Setup details are in [Self-Hosted CI/CD](docs/ci-cd.md).

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

Then open `http://localhost:8080/`, enter `drift-demo` in Kubernetes namespaces, click **Check Kubernetes integration**, select the Kubernetes collector, and capture a baseline.

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
- Remediation plans are generated separately from execution and can require approval; noop execution is reported as simulation only.
- Scheduled scan jobs, audit events, and remediation approvals are durable and API-visible.
- Storage adapters support in-memory testing, Postgres, Redis, and Elasticsearch.
- Events, metrics, traces, correlation IDs, and structured logging are first-class.

## API Security

Production service accounts are JSON records with explicit scopes. Use `X-API-Key` to authenticate API calls.

```json
[{"id":"platform-ops","key":"replace-me","scopes":["baseline:write","scan:execute","jobs:write","audit:read"]}]
```

Available write scopes include `baseline:write`, `scan:execute`, `policy:write`, `jobs:write`, `remediation:plan`, `remediation:approve`, `remediation:execute`, and `audit:read`.

Staging and production require `DRIFT_AUTH_REQUIRED=true` plus `DRIFT_SERVICE_ACCOUNTS` or `DRIFT_API_KEYS`. `DRIFT_ALLOW_DEV_AUTH=true` is rejected outside local development.
