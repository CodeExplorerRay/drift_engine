import type {
  Baseline,
  DashboardData,
  DriftReport,
  RemediationAction,
  RemediationCapability,
  ScheduledJob
} from "../../types";
import { Badge, toneForSeverity, toneForStatus } from "../Badge";
import { Button } from "../Button";
import { EmptyState } from "../EmptyState";
import { findingTotal, formatTime, shortId } from "./shared";

function reportForAction(action: RemediationAction, reports: DriftReport[]): string | null {
  const report = reports.find((item) =>
    item.findings.some((finding) => finding.id === action.finding_id)
  );
  return report?.id ?? null;
}

export function SectionError({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-red-500/20 bg-red-950/20 p-4">
      <Badge tone="danger">Failed to load</Badge>
      <p className="mt-2 text-sm leading-6 text-slate-300">{message}</p>
    </div>
  );
}

export function FindingsTable({
  error,
  report
}: {
  error: string | null;
  report: DriftReport | null;
}) {
  if (error) {
    return <SectionError message={error} />;
  }
  const findings = report?.findings ?? [];
  if (!findings.length) {
    return <EmptyState message="No findings for the selected report." />;
  }
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead>
          <tr className="border-b border-white/5 text-xs uppercase tracking-[0.12em] text-slate-500">
            <th className="py-3 pr-4 font-semibold">Resource</th>
            <th className="px-4 py-3 font-semibold">Severity</th>
            <th className="px-4 py-3 font-semibold">Type</th>
            <th className="px-4 py-3 font-semibold">Path</th>
            <th className="py-3 pl-4 font-semibold">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {findings.map((finding) => (
            <tr className="align-top" key={finding.id}>
              <td className="max-w-md py-4 pr-4">
                <p className="font-medium text-white">{shortId(finding.resource_key, 82)}</p>
                <p className="mt-1 font-mono text-xs text-slate-500">
                  {shortId(finding.fingerprint, 32)}
                </p>
              </td>
              <td className="px-4 py-4">
                <div className="flex flex-wrap gap-2">
                  <Badge tone={toneForSeverity(finding.severity)}>{finding.severity}</Badge>
                  {finding.trusted === false ? <Badge tone="warning">Untrusted</Badge> : null}
                </div>
              </td>
              <td className="px-4 py-4 text-slate-300">
                {finding.drift_type} · {finding.resource_type}
              </td>
              <td className="px-4 py-4 font-mono text-xs text-slate-400">
                {finding.path || "/"}
              </td>
              <td className="py-4 pl-4">
                <Badge tone={toneForStatus(finding.status)}>{finding.status}</Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ReportsTable({
  canExecuteRemediation,
  error,
  executeDisabledReason,
  executionLabel,
  loading,
  reports,
  selectedReportId,
  setSelectedReportId,
  onExecute,
  onPlan
}: {
  canExecuteRemediation: boolean;
  error: string | null;
  executeDisabledReason: string | null;
  executionLabel: string;
  loading: boolean;
  reports: DriftReport[];
  selectedReportId: string | null;
  setSelectedReportId: (reportId: string) => void;
  onExecute: (reportId: string | null) => void;
  onPlan: (reportId: string | null) => void;
}) {
  if (error) {
    return <SectionError message={error} />;
  }
  if (!reports.length) {
    return <EmptyState message="No drift reports yet. Run a scan to populate report history." />;
  }
  return (
    <div className="space-y-3">
      {!canExecuteRemediation && executeDisabledReason ? (
        <p className="text-xs leading-5 text-slate-500">{executeDisabledReason}</p>
      ) : null}
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
        <thead>
          <tr className="border-b border-white/5 text-xs uppercase tracking-[0.12em] text-slate-500">
            <th className="py-3 pr-4 font-semibold">Report</th>
            <th className="px-4 py-3 font-semibold">Risk</th>
            <th className="px-4 py-3 font-semibold">Findings</th>
            <th className="px-4 py-3 font-semibold">Generated</th>
            <th className="py-3 pl-4 font-semibold">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {reports.map((report) => (
            <tr key={report.id}>
              <td className="py-4 pr-4">
                <p className="font-medium text-white">{shortId(report.id, 18)}</p>
                <p className="mt-1 font-mono text-xs text-slate-500">
                  baseline {shortId(report.baseline_id, 22)}
                </p>
              </td>
              <td className="px-4 py-4">
                <Badge tone={report.risk_score >= 70 ? "danger" : "warning"}>
                  {String(Math.round(report.risk_score))}
                </Badge>
              </td>
              <td className="px-4 py-4 text-slate-300">{findingTotal(report)}</td>
              <td className="px-4 py-4 text-slate-300">{formatTime(report.generated_at)}</td>
              <td className="py-4 pl-4">
                <div className="flex flex-wrap gap-2">
                  <Button
                    disabled={loading || report.id === selectedReportId}
                    onClick={() => setSelectedReportId(report.id)}
                    variant="ghost"
                  >
                    {report.id === selectedReportId ? "Selected" : "Select"}
                  </Button>
                  <Button disabled={loading} onClick={() => onPlan(report.id)}>
                    Plan
                  </Button>
                  <Button
                    disabled={loading || !canExecuteRemediation}
                    onClick={() => onExecute(report.id)}
                    variant="warning"
                  >
                    {executionLabel}
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
        </table>
      </div>
    </div>
  );
}

export function RemediationTable({
  actions,
  canExecuteRemediation,
  error,
  executionLabel,
  loading,
  remediationCapability,
  reports,
  onApprove,
  onExecute
}: {
  actions: RemediationAction[];
  canExecuteRemediation: boolean;
  error: string | null;
  executionLabel: string;
  loading: boolean;
  remediationCapability: RemediationCapability;
  reports: DriftReport[];
  onApprove: (actionId: string) => void;
  onExecute: (reportId: string | null) => void;
}) {
  if (error) {
    return <SectionError message={error} />;
  }
  if (!actions.length) {
    return <EmptyState message="No remediation plan yet. Plan remediation from a drift report first." />;
  }
  return (
    <div className="grid gap-3">
      <div className="rounded-2xl border border-white/5 bg-black/20 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={remediationCapability.can_execute ? "info" : "warning"}>
            {`Executor ${remediationCapability.executor_mode}`}
          </Badge>
          {remediationCapability.simulation_only ? (
            <Badge tone="warning">Simulation only</Badge>
          ) : (
            <Badge tone="good">Real execution available</Badge>
          )}
        </div>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          The dashboard only labels execution as real when the backend exposes a real executor.
        </p>
      </div>
      {actions.map((action) => {
        const reportId = reportForAction(action, reports);
        const isApproved = ["approved", "skipped", "succeeded"].includes(action.status);
        const canApproveAction = action.requires_approval && !isApproved;
        const canExecuteAction =
          canExecuteRemediation &&
          Boolean(reportId) &&
          (!action.requires_approval || isApproved);
        const approveLabel = !action.requires_approval
          ? "Approval not required"
          : isApproved
            ? "Approved"
            : "Approve action";
        const executeLabel = !reportId
          ? "Report unavailable"
          : action.requires_approval && !isApproved
            ? "Approve before execute"
            : executionLabel;
        return (
          <div
            className="grid gap-4 rounded-2xl border border-white/5 bg-black/20 p-4 lg:grid-cols-[1fr_auto]"
            key={action.id}
          >
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={toneForStatus(action.status)}>{action.status}</Badge>
                <span className="text-sm font-semibold text-white">{action.strategy}</span>
                {action.simulated ? <Badge tone="warning">Simulated</Badge> : null}
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-300">{action.description}</p>
              <p className="mt-2 text-xs text-slate-400">
                Risk {Math.round(action.risk_score)} · Dry run {action.dry_run ? "enabled" : "off"} ·
                Approval {action.requires_approval ? "required" : "automatic"}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button disabled={loading || !canApproveAction} onClick={() => onApprove(action.id)}>
                {approveLabel}
              </Button>
              <Button
                disabled={loading || !canExecuteAction}
                onClick={() => onExecute(reportId)}
                variant="warning"
              >
                {executeLabel}
              </Button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function BaselinesTable({
  baselines,
  error
}: {
  baselines: Baseline[];
  error: string | null;
}) {
  if (error) {
    return <SectionError message={error} />;
  }
  if (!baselines.length) {
    return <EmptyState message="No baselines yet. Capture one from the current collected state." />;
  }
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead>
          <tr className="border-b border-white/5 text-xs uppercase tracking-[0.12em] text-slate-500">
            <th className="py-3 pr-4 font-semibold">Baseline</th>
            <th className="px-4 py-3 font-semibold">Version</th>
            <th className="px-4 py-3 font-semibold">Resources</th>
            <th className="px-4 py-3 font-semibold">Checksum</th>
            <th className="py-3 pl-4 font-semibold">Created</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {baselines.map((baseline) => (
            <tr key={baseline.id}>
              <td className="py-4 pr-4">
                <p className="font-medium text-white">{baseline.name}</p>
                <p className="mt-1 font-mono text-xs text-slate-500">
                  {shortId(baseline.id, 24)}
                </p>
              </td>
              <td className="px-4 py-4 text-slate-300">{baseline.version}</td>
              <td className="px-4 py-4 text-slate-300">
                {Object.keys(baseline.resources || {}).length}
              </td>
              <td className="px-4 py-4 font-mono text-xs text-slate-400">
                {shortId(baseline.checksum, 28)}
              </td>
              <td className="py-4 pl-4 text-slate-300">{formatTime(baseline.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function JobsTable({
  error,
  jobs,
  loading,
  onRunJob
}: {
  error: string | null;
  jobs: ScheduledJob[];
  loading: boolean;
  onRunJob: (jobId: string) => void;
}) {
  if (error) {
    return <SectionError message={error} />;
  }
  if (!jobs.length) {
    return <EmptyState message="No scheduled jobs yet. Create one from the quick actions panel." />;
  }
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead>
          <tr className="border-b border-white/5 text-xs uppercase tracking-[0.12em] text-slate-500">
            <th className="py-3 pr-4 font-semibold">Job</th>
            <th className="px-4 py-3 font-semibold">Interval</th>
            <th className="px-4 py-3 font-semibold">Next run</th>
            <th className="px-4 py-3 font-semibold">Last run</th>
            <th className="py-3 pl-4 font-semibold">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {jobs.map((job) => (
            <tr key={job.id}>
              <td className="py-4 pr-4">
                <p className="font-medium text-white">{job.name}</p>
                <p className="mt-1 font-mono text-xs text-slate-500">{shortId(job.id, 24)}</p>
              </td>
              <td className="px-4 py-4 text-slate-300">{job.interval_seconds}s</td>
              <td className="px-4 py-4 text-slate-300">{formatTime(job.next_run_at)}</td>
              <td className="px-4 py-4 text-slate-300">{formatTime(job.last_run_at)}</td>
              <td className="py-4 pl-4">
                <Button disabled={loading} onClick={() => onRunJob(job.id)}>
                  Run now
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function IntegrationsGrid({
  data,
  error
}: {
  data: DashboardData;
  error: string | null;
}) {
  if (error) {
    return <SectionError message={error} />;
  }
  if (!data.integrations.length) {
    return <EmptyState message="No integrations are configured." />;
  }
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {data.integrations.map((integration) => (
        <div className="rounded-2xl border border-white/5 bg-black/20 p-4" key={integration.name}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-semibold text-white">
                {integration.display_name || integration.name}
              </p>
              <p className="mt-1 text-xs text-slate-500">{integration.collector_name}</p>
            </div>
            <Badge tone={toneForStatus(integration.status)}>{integration.status}</Badge>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-300">{integration.description}</p>
          <p className="mt-3 text-xs leading-5 text-slate-400">
            Missing: {integration.missing.length ? integration.missing.join(", ") : "None"}
          </p>
        </div>
      ))}
    </div>
  );
}

export function AuditList({ data, error }: { data: DashboardData; error: string | null }) {
  if (error) {
    return <SectionError message={error} />;
  }
  if (!data.audit.length) {
    return <EmptyState message="No audit events yet." />;
  }
  return (
    <div className="grid gap-3">
      {data.audit.map((event) => (
        <div
          className="grid gap-3 rounded-2xl border border-white/5 bg-black/20 p-4 sm:grid-cols-[1fr_auto]"
          key={event.id}
        >
          <div>
            <p className="font-semibold text-white">{event.action}</p>
            <p className="mt-1 text-sm text-slate-400">
              {event.actor_id} changed {event.target_type} {shortId(event.target_id, 24)}
            </p>
          </div>
          <p className="text-sm text-slate-400">{formatTime(event.created_at)}</p>
        </div>
      ))}
    </div>
  );
}
