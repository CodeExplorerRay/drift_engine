import type {
  AuditEvent,
  Baseline,
  Collector,
  DashboardData,
  DriftReport,
  HealthResponse,
  Integration,
  KubernetesCheck,
  RemediationAction,
  ScheduledJob
} from "./types";

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
    throw new Error(String(detail));
  }
  return body as T;
}

async function optional<T>(path: string, fallback: T): Promise<T> {
  try {
    return await request<T>(path);
  } catch {
    return fallback;
  }
}

export async function loadDashboard(): Promise<DashboardData> {
  const [health, collectors, integrations, baselines, reports, jobs, actions, audit] =
    await Promise.all([
      optional<HealthResponse>("/health/ready", {
        status: "not_ready",
        service: "system-drift-engine",
        version: "unknown"
      }),
      optional<Collector[]>("/collectors", []),
      optional<Integration[]>("/integrations", []),
      optional<Baseline[]>("/baselines", []),
      optional<DriftReport[]>("/drifts?limit=50", []),
      optional<ScheduledJob[]>("/jobs", []),
      optional<RemediationAction[]>("/remediation/actions", []),
      optional<AuditEvent[]>("/audit?limit=50", [])
    ]);
  return { health, collectors, integrations, baselines, reports, jobs, actions, audit };
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
