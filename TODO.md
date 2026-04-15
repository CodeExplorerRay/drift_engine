# Production Hardening TODO

This list keeps the System Drift Engine hardening work ordered and auditable.

## Phase 1: Runtime Durability

- [x] Replace API in-memory repositories with durable storage when `DRIFT_DATABASE_URL` is configured.
- [x] Manage database engine/session lifecycle through FastAPI startup/shutdown.
- [x] Commit repository writes and rollback failed write units.
- [x] Verify baselines, snapshots, reports, and policies survive API process restarts.
- [x] Add readiness checks for database connectivity and schema availability.

## Phase 2: Security Baseline

- [x] Split local Docker settings from production deployment settings.
- [x] Enable authentication by default outside local development.
- [x] Replace static API key-only auth with scoped users/service accounts.
- [x] Add RBAC for baseline writes, policy writes, scan execution, and remediation execution.
- [x] Add durable audit logs for write operations and security-relevant events.

## Phase 3: Continuous Operations

- [x] Wire the scheduler into the API lifecycle.
- [x] Persist scheduled scan jobs and execution history.
- [x] Add distributed locking for multi-replica deployments.
- [x] Expose job status and recent scan history through API/UI.

## Phase 4: Remediation Governance

- [x] Persist remediation plans and actions.
- [x] Require explicit approval records before executing non-dry-run remediation.
- [x] Add approval expiry, approver identity, and idempotency keys.
- [x] Replace raw shell-command remediation with named, allow-listed runbook actions.

## Phase 5: Collector Maturity

- [x] Normalize Windows service output instead of storing raw JSON blobs.
- [x] Normalize network listeners instead of storing raw command output.
- [x] Make volatile file attributes such as `mtime_ns` configurable or ignored by default.
- [x] Expand AWS, Azure, and Kubernetes collector coverage with pagination and retries.
- [x] Add recorded fixture tests for cloud/Kubernetes collectors.

## Phase 6: CI And Release Quality

- [x] Make `ruff`, `pytest`, `mypy`, Docker build, and migration checks required.
- [x] Add coverage thresholds and publish coverage reports.
- [x] Add dependency and container vulnerability scanning on a supported Python version.
- [x] Add production deployment documentation and rollback procedures.

## Phase 7: Integration Readiness

- [x] Add environment-driven enablement for Kubernetes, AWS, and Azure integrations.
- [x] Surface integration readiness, missing dependencies, and setup guidance through API.
- [x] Show integration status in the browser dashboard so operators understand what is being collected.
- [x] Document integration setup and scoping options for real infrastructure targets.
- [x] Add tests for integration configuration and API visibility.

## Phase 8: Kubernetes Integration Readiness

- [x] Add a Kubernetes readiness check endpoint for kubectl, context, namespace access, and workload read permissions.
- [x] Allow baseline capture and drift scans to pass Kubernetes namespace scope.
- [x] Expand Kubernetes collection to include all selected namespaces and RBAC/service-account resources.
- [x] Add Kubernetes-specific policy rules for public exposure, workload spec changes, replica drift, and RBAC drift.
- [x] Add browser dashboard controls for namespace scoping and Kubernetes readiness checks.
- [x] Add local Kubernetes demo manifests that intentionally create drift.
- [x] Add tests for Kubernetes integration checks, scoped collector behavior, policies, and API visibility.

## Phase 9: Operator Dashboard

- [x] Add report history with inspect and remediation-plan actions.
- [x] Add scheduled scan job creation and manual run controls.
- [x] Add remediation queue visibility for generated actions.
- [x] Add remediation approval and approved execution controls.
- [x] Add audit trail visibility for authorized operators.
- [x] Add dashboard refresh flow for production API-key sessions.

## Phase 10: Self-Hosted CI/CD

- [x] Add a no-billing Docker Compose CI server option.
- [x] Add a Woodpecker pipeline for lint, type checks, tests, coverage, migration checks, API smoke checks, and Docker build validation.
- [x] Document GitHub and GitLab self-hosted CI setup.
- [x] Keep CI secrets out of the repository and document local environment variables.

## Phase 11: Live Kubernetes Validation

- [ ] Install or start a real local Kubernetes cluster with kind, minikube, or Docker Desktop Kubernetes.
- [ ] Apply `examples/kubernetes/baseline.yaml`.
- [ ] Capture a Kubernetes baseline from the live cluster.
- [ ] Apply `examples/kubernetes/drift.yaml`.
- [ ] Run a drift scan and record the actual detected deployment, service, and RBAC findings.

## Phase 12: Production Safety Corrections

- [x] Make local development auth fallback require `DRIFT_ALLOW_DEV_AUTH=true`.
- [x] Refuse startup in staging/production without configured service accounts or API keys.
- [x] Remove `/metrics` from unauthenticated bypasses and restrict metrics access by environment/network.
- [x] Expose remediation executor capability and label noop execution as simulation-only.
- [x] Mark partial collector scans as non-authoritative and flag untrusted removed-resource findings.
- [x] Preserve dashboard section load failures instead of converting them into empty data.
- [x] Bound list endpoints, baseline payload sizes, collector scopes, and remediation execution idempotency.
- [x] Split dashboard table rendering out of `App.tsx` and move backend runtime composition helpers out of dependencies.
