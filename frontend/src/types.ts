export type HealthResponse = {
  status: string;
  service: string;
  version: string;
  details?: {
    environment?: string;
    storage_backend?: string;
    database?: string;
  };
};

export type Collector = {
  name: string;
  enabled: boolean;
  resource_type: string;
  integration: string;
  status: string;
  description: string;
};

export type Integration = {
  name: string;
  display_name: string;
  collector_name: string;
  description: string;
  enabled: boolean;
  status: string;
  resource_types: string[];
  optional_dependencies: string[];
  required_configuration: string[];
  missing: string[];
  setup_hint: string;
};

export type Baseline = {
  id: string;
  name: string;
  version: string;
  resources: Record<string, Record<string, unknown>>;
  scope: Record<string, unknown>;
  metadata: Record<string, unknown>;
  checksum: string;
  signature: string | null;
  created_at: string;
};

export type DriftFinding = {
  id: string;
  baseline_id: string;
  snapshot_id: string;
  resource_key: string;
  resource_type: string;
  drift_type: string;
  path: string;
  expected: unknown;
  actual: unknown;
  severity: string;
  risk_score: number;
  status: string;
  policy_violations: string[];
  detected_at: string;
  fingerprint: string;
};

export type DriftReport = {
  id: string;
  baseline_id: string;
  snapshot_id: string;
  generated_at: string;
  findings: DriftFinding[];
  policy_results: Record<string, unknown>[];
  risk_score: number;
  summary: {
    total?: number;
    added?: number;
    removed?: number;
    modified?: number;
    by_severity?: Record<string, number>;
  };
};

export type ScheduledJob = {
  id: string;
  name: string;
  baseline_id: string;
  collector_names: string[] | null;
  interval_seconds: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
  next_run_at: string;
  last_run_at: string | null;
};

export type RemediationAction = {
  id: string;
  finding_id: string;
  fingerprint: string;
  strategy: string;
  description: string;
  risk_score: number;
  command: string[];
  runbook_id: string | null;
  parameters: Record<string, string>;
  status: string;
  requires_approval: boolean;
  approved_by: string | null;
  approval_expires_at: string | null;
  idempotency_key: string | null;
  dry_run: boolean;
  output: string;
  error: string;
  created_at: string;
  executed_at: string | null;
};

export type AuditEvent = {
  id: string;
  actor_id: string;
  actor_type: string;
  action: string;
  target_type: string;
  target_id: string;
  details: Record<string, unknown>;
  correlation_id: string | null;
  created_at: string;
};

export type KubernetesCheck = {
  integration: string;
  ready: boolean;
  context: string | null;
  namespaces: string[];
  checks: {
    name: string;
    status: string;
    details: Record<string, unknown>;
    error: string | null;
  }[];
};

export type DashboardData = {
  health: HealthResponse;
  collectors: Collector[];
  integrations: Integration[];
  baselines: Baseline[];
  reports: DriftReport[];
  jobs: ScheduledJob[];
  actions: RemediationAction[];
  audit: AuditEvent[];
};
