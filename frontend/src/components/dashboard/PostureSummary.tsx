import { Card } from "../Card";
import { formatTime } from "./shared";

type PostureSummaryProps = {
  criticalFindings: number;
  lastScan: string | null;
  pendingApprovals: number;
  posture: string;
  unhealthyIntegrations: number;
};

export function PostureSummary({
  criticalFindings,
  lastScan,
  pendingApprovals,
  posture,
  unhealthyIntegrations
}: PostureSummaryProps) {
  const metrics = [
    { label: "Overall posture", value: posture },
    { label: "Critical findings", value: String(criticalFindings) },
    { label: "Pending approvals", value: String(pendingApprovals) },
    { label: "Unhealthy integrations", value: String(unhealthyIntegrations) },
    { label: "Last successful scan", value: formatTime(lastScan) }
  ];

  return (
    <div className="grid gap-4 md:grid-cols-5">
      {metrics.map((metric) => (
        <Card className="px-4 py-4" key={metric.label}>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            {metric.label}
          </p>
          <p className="mt-2 truncate text-2xl font-semibold tracking-[-0.04em] text-white">
            {metric.value}
          </p>
        </Card>
      ))}
    </div>
  );
}
