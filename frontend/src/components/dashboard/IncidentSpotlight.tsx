import type { DriftFinding, DriftReport } from "../../types";
import { Badge, toneForSeverity } from "../Badge";
import { Button } from "../Button";
import { Card } from "../Card";
import { formatTime, shortId } from "./shared";

type IncidentSpotlightProps = {
  finding: DriftFinding | null;
  report: DriftReport | null;
  onPlan: () => void;
  onSelectTab: () => void;
};

export function IncidentSpotlight({
  finding,
  report,
  onPlan,
  onSelectTab
}: IncidentSpotlightProps) {
  if (!report) {
    return (
      <Card className="p-6">
        <Badge tone="info">No scan yet</Badge>
        <h2 className="mt-4 text-2xl font-semibold tracking-[-0.04em] text-white">
          Capture a baseline, then run your first drift scan.
        </h2>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
          The console will spotlight the highest-risk finding, approval needs, and the next
          recommended operator action after a scan completes.
        </p>
      </Card>
    );
  }

  if (!finding) {
    return (
      <Card className="p-6">
        <Badge tone="good">Stable</Badge>
        <h2 className="mt-4 text-2xl font-semibold tracking-[-0.04em] text-white">
          No drift findings in the selected report.
        </h2>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          Latest scan completed at {formatTime(report.generated_at)} with a risk score of{" "}
          {Math.round(report.risk_score)}.
        </p>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden border-red-500/20 bg-gradient-to-br from-red-950/35 via-[#11161d] to-[#11161d]">
      <div className="border-b border-white/5 px-6 py-5">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone={toneForSeverity(finding.severity)}>{finding.severity}</Badge>
          <span className="text-sm font-medium text-slate-400">
            Risk {Math.round(finding.risk_score)} · {finding.drift_type}
          </span>
        </div>
        <h2 className="mt-4 max-w-4xl text-2xl font-semibold tracking-[-0.04em] text-white sm:text-3xl">
          {finding.resource_type} drift requires operator review.
        </h2>
        <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-400">
          {shortId(finding.resource_key, 120)} changed at{" "}
          <span className="font-mono text-slate-200">{finding.path || "/"}</span>. Review the
          finding details, create a remediation plan, then approve only the safe actions.
        </p>
      </div>
      <div className="grid gap-4 bg-black/10 px-6 py-5 lg:grid-cols-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
            Expected
          </p>
          <pre className="mt-2 max-h-28 overflow-auto rounded-xl bg-black/30 p-3 text-xs text-slate-300 ring-1 ring-white/5">
            {JSON.stringify(finding.expected, null, 2)}
          </pre>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
            Actual
          </p>
          <pre className="mt-2 max-h-28 overflow-auto rounded-xl bg-black/30 p-3 text-xs text-slate-300 ring-1 ring-white/5">
            {JSON.stringify(finding.actual, null, 2)}
          </pre>
        </div>
        <div className="flex flex-col justify-between gap-4 rounded-xl border border-white/5 bg-black/20 p-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
              Next action
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              Prioritize this finding before routine baseline and integration work.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={onPlan} variant="primary">
              Plan remediation
            </Button>
            <Button onClick={onSelectTab}>Open findings</Button>
          </div>
        </div>
      </div>
    </Card>
  );
}
