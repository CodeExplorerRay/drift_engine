import type {
  AuditEvent,
  Baseline,
  Collector,
  DashboardData,
  DashboardSection,
  DriftReport,
  HealthResponse,
  Integration,
  KubernetesCheck,
  RemediationCapability,
  RemediationAction,
  ScheduledJob
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly path: string,
    readonly correlationId: string | null = null
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers
    }
  });
  const text = await response.text();
  const body = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail =
      typeof body === "object" && body !== null
        ? body.detail || body.error || JSON.stringify(body)
        : response.statusText;
    const correlationId =
      typeof body === "object" && body !== null && "correlation_id" in body
        ? String(body.correlation_id)
        : null;
    throw new ApiError(String(detail), response.status, path, correlationId);
  }
  return body as T;
}

async function loadSection<T>(
  section: DashboardSection,
  path: string,
  fallback: T
): Promise<{ data: T; error: Partial<Record<DashboardSection, string>> }> {
  try {
    return { data: await request<T>(path), error: {} };
  } catch (error) {
    const message = error instanceof Error ? error.message : "failed to load";
    return { data: fallback, error: { [section]: message } };
  }
}

export async function loadDashboard(): Promise<DashboardData> {
  const [
    health,
    collectors,
    integrations,
    baselines,
    reports,
    jobs,
    actions,
    audit,
    remediationCapability
  ] =
    await Promise.all([
      loadSection<HealthResponse>("health", "/health/ready", {
        status: "not_ready",
        service: "system-drift-engine",
        version: "unknown"
      }),
      loadSection<Collector[]>("collectors", "/collectors", []),
      loadSection<Integration[]>("integrations", "/integrations", []),
      loadSection<Baseline[]>("baselines", "/baselines", []),
      loadSection<DriftReport[]>("reports", "/drifts?limit=50", []),
      loadSection<ScheduledJob[]>("jobs", "/jobs?limit=100", []),
      loadSection<RemediationAction[]>("actions", "/remediation/actions", []),
      loadSection<AuditEvent[]>("audit", "/audit?limit=50", []),
      loadSection<RemediationCapability>("remediationCapability", "/remediation/capability", {
        enabled: false,
        dry_run: true,
        executor_mode: "unknown",
        real_execution_available: false,
        simulation_only: true,
        can_execute: false
      })
    ]);
  const errors = {
    ...health.error,
    ...collectors.error,
    ...integrations.error,
    ...baselines.error,
    ...reports.error,
    ...jobs.error,
    ...actions.error,
    ...audit.error,
    ...remediationCapability.error
  };
  return {
    health: health.data,
    collectors: collectors.data,
    integrations: integrations.data,
    baselines: baselines.data,
    reports: reports.data,
    jobs: jobs.data,
    actions: actions.data,
    audit: audit.data,
    remediationCapability: remediationCapability.data,
    errors,
    loaded_at: new Date().toISOString()
  };
}

export function captureBaseline(payload: {
  name: string;
  version: string;
  collector_names: string[] | null;
}): Promise<Baseline> {
  return request<Baseline>("/baselines/from-current", {
    method: "POST",
    body: JSON.stringify({
      ...payload,
      metadata: { created_from: "react-operator-console" }
    })
  });
}

export function runDriftScan(payload: {
  baseline_id: string;
  collector_names: string[] | null;
  auto_remediate: boolean;
}): Promise<DriftReport> {
  return request<DriftReport>("/drifts/run", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function createJob(payload: {
  name: string;
  baseline_id: string;
  interval_seconds: number;
  collector_names: string[] | null;
}): Promise<ScheduledJob> {
  return request<ScheduledJob>("/jobs", {
    method: "POST",
    body: JSON.stringify({ ...payload, enabled: true })
  });
}

export function checkKubernetes(namespaces: string): Promise<KubernetesCheck> {
  const query = namespaces ? `?namespaces=${encodeURIComponent(namespaces)}` : "";
  return request<KubernetesCheck>(`/integrations/kubernetes/check${query}`);
}

export function planRemediation(reportId: string): Promise<unknown> {
  return request(`/remediation/reports/${encodeURIComponent(reportId)}/plan`, {
    method: "POST"
  });
}

export function approveAction(actionId: string): Promise<RemediationAction> {
  return request<RemediationAction>(`/remediation/actions/${encodeURIComponent(actionId)}/approve`, {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function executeRemediation(reportId: string): Promise<RemediationAction[]> {
  return request<RemediationAction[]>(`/remediation/reports/${encodeURIComponent(reportId)}/execute`, {
    method: "POST",
    headers: {
      "Idempotency-Key": crypto.randomUUID()
    }
  });
}

export function runJobNow(jobId: string): Promise<{ id: string; report_id: string | null }> {
  return request<{ id: string; report_id: string | null }>(`/jobs/${encodeURIComponent(jobId)}/run`, {
    method: "POST"
  });
}
