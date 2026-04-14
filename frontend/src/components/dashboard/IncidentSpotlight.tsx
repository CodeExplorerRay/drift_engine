import type { DriftFinding, DriftReport } from "../../types";
import { Badge, toneForSeverity } from "../Badge";
import { Button } from "../Button";
import { Card } from "../Card";
import { findingTotal, formatTime, humanizeLabel, shortId } from "./shared";

type IncidentSpotlightProps = {
  environment: string | null;
  finding: DriftFinding | null;
  report: DriftReport | null;
  onOpenFindings: () => void;
  onPlan: () => void;
};

export function IncidentSpotlight({
  environment,
  finding,
  report,
  onOpenFindings,
  onPlan
}: IncidentSpotlightProps) {
  if (!report) {
    return (
      <Card className="p-6">
        <Badge tone="info">No scan yet</Badge>
        <h2 className="mt-4 text-2xl font-semibold tracking-[-0.04em] text-white">
          Capture a baseline, then run your first honest scan.
        </h2>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
          This console only promotes real findings from the backend. Once a report exists, the
          spotlight will show the highest-risk drift, the affected resource, and the next operator
          step.
        </p>
      </Card>
    );
  }

  if (!finding) {
    return (
      <Card className="p-6">
        <Badge tone="good">Stable</Badge>
        <h2 className="mt-4 text-2xl font-semibold tracking-[-0.04em] text-white">
          No urgent drift in the selected report.
        </h2>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          Report {shortId(report.id, 18)} completed at {formatTime(report.generated_at)} with risk{" "}
          {Math.round(report.risk_score)} and {findingTotal(report)} total findings.
        </p>
      </Card>
    );
  }

  const scope = (environment || "current environment").toLowerCase();
  const severity = finding.severity.toLowerCase();
  const eyebrow = ["critical", "high"].includes(severity) ? "Critical Incident" : "Incident Spotlight";
  const title = `${humanizeLabel(finding.resource_type)} drift in ${scope}`;
  const reportSummary = `${findingTotal(report)} finding${findingTotal(report) === 1 ? "" : "s"} in report ${shortId(report.id, 18)}`;

  return (
    <Card className="overflow-hidden border-red-500/20 bg-gradient-to-br from-red-950/35 via-[#11161d] to-[#11161d]">
      <div className="border-b border-white/5 px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-red-300">{eyebrow}</p>
        <h2 className="mt-4 max-w-4xl text-2xl font-semibold tracking-[-0.04em] text-white sm:text-3xl">
          {title}
        </h2>
        <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-400">
          {reportSummary}. Highest-risk resource {shortId(finding.resource_key, 120)} drifted at{" "}
          <span className="font-mono text-slate-200">{finding.path || "$"}</span>. Review the
          evidence, plan remediation, and approve only the actions you intend to run.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Badge tone={toneForSeverity(finding.severity)}>{finding.severity}</Badge>
          <Badge tone="warning">{`Risk ${Math.round(finding.risk_score)}`}</Badge>
          <Badge tone="info">{finding.drift_type}</Badge>
          <Badge tone="neutral">{`Baseline ${shortId(report.baseline_id, 16)}`}</Badge>
        </div>
        <div className="mt-5 flex flex-wrap gap-3">
          <Button onClick={onOpenFindings} variant="primary">
            Open report
          </Button>
          <Button onClick={onPlan}>Plan remediation</Button>
        </div>
      </div>
      <div className="grid gap-4 bg-black/10 px-6 py-5 lg:grid-cols-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Expected</p>
          <pre className="mt-2 max-h-28 overflow-auto rounded-xl bg-black/30 p-3 text-xs text-slate-300 ring-1 ring-white/5">
            {JSON.stringify(finding.expected, null, 2)}
          </pre>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Actual</p>
          <pre className="mt-2 max-h-28 overflow-auto rounded-xl bg-black/30 p-3 text-xs text-slate-300 ring-1 ring-white/5">
            {JSON.stringify(finding.actual, null, 2)}
          </pre>
        </div>
        <div className="flex flex-col justify-between gap-4 rounded-xl border border-white/5 bg-black/20 p-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Next action</p>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              Start with the selected report, confirm whether the baseline is still authoritative,
              then generate remediation from the real finding set instead of acting on assumptions.
            </p>
          </div>
          <p className="text-xs leading-5 text-slate-400">Last scan {formatTime(report.generated_at)}</p>
        </div>
      </div>
    </Card>
  );
}
