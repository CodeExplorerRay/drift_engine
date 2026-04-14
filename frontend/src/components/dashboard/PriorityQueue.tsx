import type { DriftFinding, DriftReport, RemediationAction } from "../../types";
import { Badge, type BadgeTone, toneForSeverity } from "../Badge";
import { Button } from "../Button";
import { Card, SectionHeader } from "../Card";
import { EmptyState } from "../EmptyState";
import { findingTotal, shortId } from "./shared";

type PriorityQueueProps = {
  actions: RemediationAction[];
  finding: DriftFinding | null;
  integrations: number;
  report: DriftReport | null;
  onApprove: (actionId: string) => void;
  onPlan: () => void;
};

type PriorityRow = {
  action: string;
  detail: string;
  onClick: () => void;
  title: string;
  tone: BadgeTone;
};

export function PriorityQueue({
  actions,
  finding,
  integrations,
  report,
  onApprove,
  onPlan
}: PriorityQueueProps) {
  const rows = [
    finding
      ? {
          title: `${finding.severity} ${finding.resource_type} drift`,
          detail: shortId(finding.resource_key, 92),
          tone: toneForSeverity(finding.severity),
          action: "Review finding",
          onClick: onPlan
        }
      : null,
    actions[0]
      ? {
          title: "Approval waiting",
          detail: actions[0].description,
          tone: "warning" as const,
          action: "Approve action",
          onClick: () => onApprove(actions[0].id)
        }
      : null,
    integrations > 0
      ? {
          title: "Integration health degraded",
          detail: `${integrations} enabled integration(s) need configuration or readiness review.`,
          tone: "warning" as const,
          action: "Inspect",
          onClick: onPlan
        }
      : null,
    report && findingTotal(report) === 0
      ? {
          title: "No open drift in latest report",
          detail: `Report ${shortId(report.id, 16)} completed cleanly.`,
          tone: "good" as const,
          action: "Keep monitoring",
          onClick: onPlan
        }
      : null
  ].filter((row): row is PriorityRow => row !== null);

  return (
    <Card>
      <SectionHeader
        eyebrow="Priority queue"
        title="What needs attention now"
        description="The queue intentionally highlights only urgent operational work."
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
