import type { DriftFinding, DriftReport, Integration, RemediationAction, ScheduledJob } from "../../types";
import { Badge, type BadgeTone, toneForSeverity } from "../Badge";
import { Button } from "../Button";
import { Card, SectionHeader } from "../Card";
import { EmptyState } from "../EmptyState";
import { findingTotal, humanizeLabel, shortId } from "./shared";

type PriorityQueueProps = {
  criticalFindings: number;
  finding: DriftFinding | null;
  integrations: Integration[];
  jobs: ScheduledJob[];
  pendingApprovals: RemediationAction[];
  report: DriftReport | null;
  onOpenFindings: () => void;
  onOpenIntegrations: () => void;
  onOpenJobs: () => void;
  onOpenRemediation: () => void;
};

type PriorityRow = {
  action: string;
  detail: string;
  onClick: () => void;
  title: string;
  tone: BadgeTone;
};

export function PriorityQueue({
  criticalFindings,
  finding,
  integrations,
  jobs,
  pendingApprovals,
  report,
  onOpenFindings,
  onOpenIntegrations,
  onOpenJobs,
  onOpenRemediation
}: PriorityQueueProps) {
  const reportFindings = findingTotal(report);
  const highestFindingTitle =
    criticalFindings > 0
      ? `${criticalFindings} critical finding${criticalFindings === 1 ? "" : "s"}`
      : reportFindings > 0
        ? `${reportFindings} finding${reportFindings === 1 ? "" : "s"} awaiting review`
        : null;

  const rows = [
    report?.scan_completeness === "partial"
      ? {
          title: "Selected report is partial",
          detail:
            report.integrity_warnings[0] ??
            "Collector failures mean this scan should not be treated as authoritative.",
          tone: "warning" as const,
          action: "Open report",
          onClick: onOpenFindings
        }
      : null,
    highestFindingTitle && finding
      ? {
          title: highestFindingTitle,
          detail: `${humanizeLabel(finding.resource_type)} drift at ${finding.path || "$"} · ${shortId(finding.resource_key, 80)}`,
          tone: toneForSeverity(finding.severity),
          action: "Open report",
          onClick: onOpenFindings
        }
      : null,
    pendingApprovals[0]
      ? {
          title: `${pendingApprovals.length} approval${pendingApprovals.length === 1 ? "" : "s"} pending`,
          detail: pendingApprovals[0].description,
          tone: "warning" as const,
          action: "Review approvals",
          onClick: onOpenRemediation
        }
      : null,
    integrations.length > 0
      ? {
          title: `${integrations.length} integration${integrations.length === 1 ? "" : "s"} degraded`,
          detail: integrations
            .slice(0, 2)
            .map((integration) => integration.display_name || integration.name)
            .join(", "),
          tone: "warning" as const,
          action: "Inspect",
          onClick: onOpenIntegrations
        }
      : null,
    jobs.length > 0
      ? {
          title: `${jobs.length} scheduled job${jobs.length === 1 ? "" : "s"} overdue`,
          detail: `${jobs[0].name} is past its next run window.`,
          tone: "warning" as const,
          action: "Open jobs",
          onClick: onOpenJobs
        }
      : null,
    report && findingTotal(report) === 0
      ? {
          title: "No urgent operator queue items",
          detail: `Latest report ${shortId(report.id, 16)} completed without open drift.`,
          tone: "good" as const,
          action: "Open report",
          onClick: onOpenFindings
        }
      : null
  ].filter((row): row is PriorityRow => row !== null);

  return (
    <Card>
      <SectionHeader
        eyebrow="Priority queue"
        title="What needs attention now"
        description="Only real, currently actionable work is promoted into this queue."
      />
      <div className="divide-y divide-white/5">
        {rows.length ? (
          rows.map((row) => (
            <div className="grid gap-4 px-5 py-4 sm:grid-cols-[1fr_auto]" key={row.title}>
              <div>
                <Badge tone={row.tone}>{row.title}</Badge>
                <p className="mt-2 text-sm leading-6 text-slate-300">{row.detail}</p>
              </div>
              <Button onClick={row.onClick}>{row.action}</Button>
            </div>
          ))
        ) : (
          <div className="p-5">
            <EmptyState message="No priority items. The next scan will repopulate this queue." />
          </div>
        )}
      </div>
    </Card>
  );
}
