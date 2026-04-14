import { Card } from "../Card";

type PostureSummaryProps = {
  criticalFindings: number;
  enabledIntegrations: number;
  overdueJobs: number;
  pendingApprovals: number;
  scheduledJobs: number;
  unhealthyIntegrations: number;
};

export function PostureSummary({
  criticalFindings,
  enabledIntegrations,
  overdueJobs,
  pendingApprovals,
  scheduledJobs,
  unhealthyIntegrations
}: PostureSummaryProps) {
  const metrics = [
    {
      label: "Critical",
      value: String(criticalFindings),
      detail: criticalFindings ? "Need immediate review" : "No urgent drift"
    },
    {
      label: "Approvals",
      value: String(pendingApprovals),
      detail: pendingApprovals ? "Waiting operator sign-off" : "No approvals pending"
    },
    {
      label: "Integrations",
      value: unhealthyIntegrations ? `${unhealthyIntegrations} degraded` : `${enabledIntegrations} ready`,
      detail: unhealthyIntegrations ? "Configuration or dependency gaps detected" : "Enabled integrations look healthy"
    },
    {
      label: "Jobs",
      value: overdueJobs ? `${overdueJobs} overdue` : scheduledJobs ? `${scheduledJobs} scheduled` : "None",
      detail: overdueJobs ? "A scheduled scan missed its window" : "No delayed recurring scans"
    }
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {metrics.map((metric) => (
        <Card className="px-4 py-4" key={metric.label}>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{metric.label}</p>
          <p className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-white">{metric.value}</p>
          <p className="mt-2 text-xs leading-5 text-slate-500">{metric.detail}</p>
        </Card>
      ))}
    </div>
  );
}
