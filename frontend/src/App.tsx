import { useEffect, useState } from "react";

import {
  approveAction,
  captureBaseline,
  checkKubernetes,
  createJob,
  executeRemediation,
  loadDashboard,
  planRemediation,
  runDriftScan,
  runJobNow
} from "./api";
import { Badge, toneForSeverity, toneForStatus } from "./components/Badge";
import { Button } from "./components/Button";
import { Card, SectionHeader } from "./components/Card";
import { IncidentSpotlight } from "./components/dashboard/IncidentSpotlight";
import { PostureSummary } from "./components/dashboard/PostureSummary";
import { PriorityQueue } from "./components/dashboard/PriorityQueue";
import { QuickActions } from "./components/dashboard/QuickActions";
import { TopStatusBar } from "./components/dashboard/TopStatusBar";
import { findingTotal, formatTime, relativeTime, shortId } from "./components/dashboard/shared";
import { EmptyState } from "./components/EmptyState";
import type {
  Baseline,
  DashboardData,
  DriftFinding,
  DriftReport,
  Integration,
  RemediationAction,
  ScheduledJob
} from "./types";

type Tab = "findings" | "reports" | "remediation" | "baselines" | "jobs" | "integrations" | "audit";

const tabs: { id: Tab; label: string }[] = [
  { id: "findings", label: "Findings" },
  { id: "reports", label: "Reports" },
  { id: "remediation", label: "Remediation" },
  { id: "baselines", label: "Baselines" },
  { id: "jobs", label: "Jobs" },
  { id: "integrations", label: "Integrations" },
  { id: "audit", label: "Audit" }
];

type TabCounts = Record<Tab, number>;

const initialData: DashboardData = {
  health: {
    status: "loading",
    service: "system-drift-engine",
    version: "unknown"
  },
  collectors: [],
  integrations: [],
  baselines: [],
  reports: [],
  jobs: [],
  actions: [],
  audit: []
};

function splitCsv(value: string): string[] | null {
  const items = value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  return items.length ? items : null;
}

function isSevere(finding: DriftFinding): boolean {
  return ["critical", "high"].includes(finding.severity.toLowerCase());
}

function reportForAction(action: RemediationAction, reports: DriftReport[]): string | null {
  const report = reports.find((item) =>
    item.findings.some((finding) => finding.id === action.finding_id)
  );
  return report?.id ?? null;
}

function isPast(value: string | null | undefined): boolean {
  if (!value) {
    return false;
  }
  const timestamp = Date.parse(value);
  return !Number.isNaN(timestamp) && timestamp <= Date.now();
}

function isEnabled(integration: Integration): boolean {
  return integration.enabled;
}

function countTabs(data: DashboardData, selectedReport: DriftReport | null): TabCounts {
  return {
    findings: findingTotal(selectedReport),
    reports: data.reports.length,
    remediation: data.actions.length,
    baselines: data.baselines.length,
    jobs: data.jobs.length,
    integrations: data.integrations.length,
    audit: data.audit.length
  };
}

function riskTone(score: number | null): "danger" | "warning" | "good" | "info" {
  if (score === null) {
    return "info";
  }
  if (score >= 70) {
    return "danger";
  }
  if (score >= 35) {
    return "warning";
  }
  return "good";
}

function selectMostUrgentFinding(report: DriftReport | null): DriftFinding | null {
  if (!report || report.findings.length === 0) {
    return null;
  }
  return [...report.findings].sort((left, right) => right.risk_score - left.risk_score)[0];
}

function App() {
  const [data, setData] = useState<DashboardData>(initialData);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("findings");
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState("Loading dashboard");
  const [baselineName, setBaselineName] = useState("prod-platform");
  const [baselineVersion, setBaselineVersion] = useState("1.0.0");
  const [collectorText, setCollectorText] = useState("file,package,kubernetes");
  const [scanAutoRemediate, setScanAutoRemediate] = useState(false);
  const [jobName, setJobName] = useState("prod-hourly");
  const [jobInterval, setJobInterval] = useState("3600");
  const [namespaces, setNamespaces] = useState("default");
  const [kubernetesStatus, setKubernetesStatus] = useState("Not checked");

  const latestReport = data.reports[0] ?? null;
  const selectedReport =
    data.reports.find((report) => report.id === selectedReportId) ?? latestReport;
  const urgentFinding = selectMostUrgentFinding(selectedReport);
  const criticalFindings = selectedReport?.findings.filter(isSevere).length ?? 0;
  const pendingApprovals = data.actions.filter((action) =>
    ["planned", "waiting_approval"].includes(action.status)
  );
  const enabledIntegrations = data.integrations.filter(isEnabled);
  const unhealthyIntegrations = data.integrations.filter(
    (integration) => integration.enabled && !["ready", "ok"].includes(integration.status)
  );
  const overdueJobs = data.jobs.filter((job) => job.enabled && isPast(job.next_run_at));
  const posture =
    criticalFindings > 0
      ? "Critical"
      : pendingApprovals.length > 0 || unhealthyIntegrations.length > 0 || overdueJobs.length > 0
        ? "Warning"
        : latestReport
          ? "Stable"
          : "Awaiting scan";
  const environment = data.health.details?.environment ?? null;
  const riskScore = selectedReport ? Math.round(selectedReport.risk_score) : null;
  const tabCounts = countTabs(data, selectedReport);

  async function refresh(quiet = false) {
    setLoading(true);
    try {
      const dashboard = await loadDashboard();
      setData(dashboard);
      if (!selectedReportId && dashboard.reports[0]) {
        setSelectedReportId(dashboard.reports[0].id);
      }
      if (!quiet) {
        setNotice("Dashboard refreshed");
      }
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Dashboard refresh failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh(true);
  }, []);

  async function perform(message: string, task: () => Promise<unknown>) {
    setLoading(true);
    try {
      await task();
      setNotice(message);
      await refresh(true);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Action failed");
    } finally {
      setLoading(false);
    }
  }

  async function onCaptureBaseline() {
    await perform("Baseline captured", async () => {
      await captureBaseline({
        name: baselineName,
        version: baselineVersion,
        collector_names: splitCsv(collectorText)
      });
    });
  }

  async function onRunScan() {
    const baselineId = selectedReport?.baseline_id ?? data.baselines[0]?.id;
    if (!baselineId) {
      setNotice("Create a baseline before running a scan");
      return;
    }
    await perform("Drift scan completed", async () => {
      const report = await runDriftScan({
        baseline_id: baselineId,
        collector_names: splitCsv(collectorText),
        auto_remediate: scanAutoRemediate
      });
      setSelectedReportId(report.id);
      setActiveTab("findings");
    });
  }

  async function onCreateJob() {
    const baselineId = selectedReport?.baseline_id ?? data.baselines[0]?.id;
    if (!baselineId) {
      setNotice("Create a baseline before scheduling a job");
      return;
    }
    await perform("Scheduled job created", async () => {
      await createJob({
        name: jobName,
        baseline_id: baselineId,
        interval_seconds: Number(jobInterval || 3600),
        collector_names: splitCsv(collectorText)
      });
    });
  }

  async function onCheckKubernetes() {
    setLoading(true);
    try {
      const result = await checkKubernetes(namespaces);
      const failed = result.checks.filter((check) => check.status !== "passed");
      setKubernetesStatus(
        result.ready
          ? `Ready on ${result.context ?? "current context"}`
          : `${failed.length || 1} check needs attention`
      );
      setNotice("Kubernetes readiness checked");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Kubernetes check failed");
    } finally {
      setLoading(false);
    }
  }

  async function onPlanRemediation(reportId: string | null) {
    if (!reportId) {
      setNotice("Select a report before planning remediation");
      return;
    }
    await perform("Remediation plan prepared", async () => {
      await planRemediation(reportId);
      setActiveTab("remediation");
    });
  }

  async function onExecuteRemediation(reportId: string | null) {
    if (!reportId) {
      setNotice("Select a report before executing remediation");
      return;
    }
    await perform("Approved remediation executed", async () => {
      await executeRemediation(reportId);
      setActiveTab("remediation");
    });
  }

  return (
    <div className="min-h-screen bg-[#0b0f14] text-slate-200">
      <div className="grid min-h-screen lg:grid-cols-[288px_minmax(0,1fr)]">
        <aside className="sticky top-0 hidden h-screen border-r border-white/5 bg-[#0f141a] px-5 py-6 lg:block">
          <div className="border-b border-white/5 pb-6">
            <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-sky-400">
              Ops Console
            </div>
            <div className="mt-3 flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded-2xl bg-white/10 text-sm font-bold text-white ring-1 ring-white/10">
                DE
              </div>
              <div>
                <h1 className="text-lg font-semibold tracking-[-0.03em] text-white">Drift Engine</h1>
                <p className="text-xs font-medium text-slate-400">Operator dashboard</p>
              </div>
            </div>
          </div>

          <div className="mt-5 rounded-2xl border border-white/5 bg-black/25 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                Live posture
              </p>
              <span
                className={[
                  "h-2 w-2 rounded-full",
                  posture === "Critical"
                    ? "bg-red-400"
                    : posture === "Warning"
                      ? "bg-amber-300"
                      : posture === "Stable"
                        ? "bg-emerald-300"
                        : "bg-sky-300"
                ].join(" ")}
              />
            </div>
            <p className="mt-3 text-lg font-semibold tracking-[-0.03em] text-white">{posture}</p>
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-400">
              <div className="rounded-xl bg-white/[0.03] px-3 py-2">
                <p className="text-slate-500">Risk</p>
                <p className="mt-1 font-semibold text-slate-200">{riskScore ?? "None"}</p>
              </div>
              <div className="rounded-xl bg-white/[0.03] px-3 py-2">
                <p className="text-slate-500">Findings</p>
                <p className="mt-1 font-semibold text-slate-200">{tabCounts.findings}</p>
              </div>
            </div>
          </div>

          <nav aria-label="Primary navigation" className="mt-6 space-y-1 text-sm">
            <a
              className="flex items-center justify-between rounded-xl px-4 py-3 font-medium text-white bg-white/10"
              href="#overview"
            >
              <span>Overview</span>
              <span className="rounded-full bg-sky-400/10 px-2 py-0.5 text-[11px] font-bold text-sky-300">
                Live
              </span>
            </a>
            {tabs.map((tab) => (
              <button
                className={[
                  "flex w-full items-center justify-between rounded-xl px-4 py-3 text-left font-medium transition",
                  activeTab === tab.id
                    ? "bg-white/10 text-white"
                    : "text-slate-400 hover:bg-white/5 hover:text-white"
                ].join(" ")}
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                type="button"
              >
                <span>{tab.label}</span>
                <span
                  className={[
                    "rounded-full px-2 py-0.5 text-[11px] font-bold",
                    activeTab === tab.id ? "bg-white/10 text-white" : "bg-black/30 text-slate-500"
                  ].join(" ")}
                >
                  {tabCounts[tab.id]}
                </span>
              </button>
            ))}
          </nav>

          <div className="absolute bottom-6 left-5 right-5 rounded-2xl border border-white/5 bg-black/20 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Status
            </p>
            <p className="mt-2 text-sm font-semibold text-white">{notice}</p>
            <p className="mt-2 text-xs leading-5 text-slate-400">
              API {data.health.status} · Storage {data.health.details?.storage_backend ?? "unknown"}
            </p>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              Last scan {relativeTime(latestReport?.generated_at ?? null)}
            </p>
          </div>
        </aside>

        <main className="min-w-0 px-4 py-4 sm:px-6 lg:px-8">
          <TopStatusBar
            environment={environment}
            health={data.health.status}
            lastScan={latestReport?.generated_at ?? null}
            loading={loading}
            onRefresh={() => refresh()}
            onRunScan={onRunScan}
            posture={posture}
            riskScore={riskScore}
          />

          <div className="mx-auto max-w-[1480px] space-y-6" id="overview">
            <PostureSummary
              criticalFindings={criticalFindings}
              enabledIntegrations={enabledIntegrations.length}
              overdueJobs={overdueJobs.length}
              pendingApprovals={pendingApprovals.length}
              scheduledJobs={data.jobs.length}
              unhealthyIntegrations={unhealthyIntegrations.length}
            />

            <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_370px]">
              <div className="space-y-5">
                <IncidentSpotlight
                  environment={environment}
                  finding={urgentFinding}
                  onOpenFindings={() => setActiveTab("findings")}
                  report={selectedReport}
                  onPlan={() => onPlanRemediation(selectedReport?.id ?? null)}
                />
                <PriorityQueue
                  criticalFindings={criticalFindings}
                  finding={urgentFinding}
                  integrations={unhealthyIntegrations}
                  jobs={overdueJobs}
                  pendingApprovals={pendingApprovals}
                  report={selectedReport}
                  onOpenFindings={() => setActiveTab("findings")}
                  onOpenIntegrations={() => setActiveTab("integrations")}
                  onOpenJobs={() => setActiveTab("jobs")}
                  onOpenRemediation={() => setActiveTab("remediation")}
                />
              </div>

              <QuickActions
                baselineName={baselineName}
                baselineVersion={baselineVersion}
                baselines={data.baselines}
                collectorText={collectorText}
                jobInterval={jobInterval}
                jobName={jobName}
                kubernetesStatus={kubernetesStatus}
                loading={loading}
                namespaces={namespaces}
                pendingApprovals={pendingApprovals.length}
                scanAutoRemediate={scanAutoRemediate}
                onBaselineNameChange={setBaselineName}
                onBaselineVersionChange={setBaselineVersion}
                onCaptureBaseline={onCaptureBaseline}
                onCheckKubernetes={onCheckKubernetes}
                onCollectorTextChange={setCollectorText}
                onCreateJob={onCreateJob}
                onExecute={() => onExecuteRemediation(selectedReport?.id ?? null)}
                onJobIntervalChange={setJobInterval}
                onJobNameChange={setJobName}
                onNamespacesChange={setNamespaces}
                onOpenRemediation={() => setActiveTab("remediation")}
                onPlan={() => onPlanRemediation(selectedReport?.id ?? null)}
                onRunScan={onRunScan}
                onScanAutoRemediateChange={setScanAutoRemediate}
              />
            </section>

            <EvidenceTabs
              activeTab={activeTab}
              data={data}
              selectedReport={selectedReport}
              selectedReportId={selectedReport?.id ?? null}
              setActiveTab={setActiveTab}
              setSelectedReportId={setSelectedReportId}
              tabCounts={tabCounts}
              onApprove={(actionId) =>
                perform("Remediation action approved", async () => {
                  await approveAction(actionId);
                })
              }
              onExecute={onExecuteRemediation}
              onPlan={onPlanRemediation}
              onRunJob={(jobId) =>
                perform("Scheduled job run completed", async () => {
                  const run = await runJobNow(jobId);
                  if (run.report_id) {
                    setSelectedReportId(run.report_id);
                  }
                })
              }
            />
          </div>
        </main>
      </div>
    </div>
  );
}

function EvidenceTabs({
  activeTab,
  data,
  selectedReport,
  selectedReportId,
  setActiveTab,
  setSelectedReportId,
  tabCounts,
  onApprove,
  onExecute,
  onPlan,
  onRunJob
}: {
  activeTab: Tab;
  data: DashboardData;
  selectedReport: DriftReport | null;
  selectedReportId: string | null;
  setActiveTab: (tab: Tab) => void;
  setSelectedReportId: (reportId: string) => void;
  tabCounts: TabCounts;
  onApprove: (actionId: string) => void;
  onExecute: (reportId: string | null) => void;
  onPlan: (reportId: string | null) => void;
  onRunJob: (jobId: string) => void;
}) {
  const selectedRisk = selectedReport ? Math.round(selectedReport.risk_score) : null;
  const generatedAt = selectedReport?.generated_at ?? null;

  return (
    <Card className="overflow-hidden" id="evidence-tabs">
      <div className="border-b border-white/5 px-5 pt-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Evidence
            </p>
            <h2 className="mt-1 text-lg font-semibold tracking-[-0.03em] text-white">
              Selected report workspace
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              {selectedReport
                ? `Report ${shortId(selectedReport.id, 22)} · baseline ${shortId(
                    selectedReport.baseline_id,
                    22
                  )} · generated ${formatTime(generatedAt)}`
                : "Run a scan to populate findings, reports, remediation, and audit evidence."}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge tone={riskTone(selectedRisk)}>
              {selectedRisk === null ? "No Risk" : `Risk ${selectedRisk}`}
            </Badge>
            <Badge tone={tabCounts.findings ? "warning" : "good"}>
              {`${tabCounts.findings} Findings`}
            </Badge>
            <Badge tone={data.actions.length ? "warning" : "neutral"}>
              {`${data.actions.length} Actions`}
            </Badge>
          </div>
        </div>

        <div className="mt-5 flex gap-2 overflow-x-auto pb-4">
          {tabs.map((tab) => (
            <button
              className={[
                "inline-flex shrink-0 items-center gap-2 rounded-xl border px-3.5 py-2.5 text-sm font-semibold transition",
                activeTab === tab.id
                  ? "border-sky-400/40 bg-sky-400/10 text-white"
                  : "border-white/5 bg-black/20 text-slate-400 hover:border-white/10 hover:bg-white/5 hover:text-white"
              ].join(" ")}
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              type="button"
            >
              <span>{tab.label}</span>
              <span
                className={[
                  "rounded-full px-2 py-0.5 text-[11px] font-bold",
                  activeTab === tab.id ? "bg-sky-300/15 text-sky-200" : "bg-white/5 text-slate-500"
                ].join(" ")}
              >
                {tabCounts[tab.id]}
              </span>
            </button>
          ))}
        </div>
      </div>
      <div className="p-5">
        {activeTab === "findings" ? <FindingsTable report={selectedReport} /> : null}
        {activeTab === "reports" ? (
          <ReportsTable
            reports={data.reports}
            selectedReportId={selectedReportId}
            setSelectedReportId={setSelectedReportId}
            onExecute={onExecute}
            onPlan={onPlan}
          />
        ) : null}
        {activeTab === "remediation" ? (
          <RemediationTable
            actions={data.actions}
            reports={data.reports}
            onApprove={onApprove}
            onExecute={onExecute}
          />
        ) : null}
        {activeTab === "baselines" ? <BaselinesTable baselines={data.baselines} /> : null}
        {activeTab === "jobs" ? <JobsTable jobs={data.jobs} onRunJob={onRunJob} /> : null}
        {activeTab === "integrations" ? <IntegrationsGrid data={data} /> : null}
        {activeTab === "audit" ? <AuditList data={data} /> : null}
      </div>
    </Card>
  );
}

function FindingsTable({ report }: { report: DriftReport | null }) {
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
                <p className="mt-1 font-mono text-xs text-slate-500">{shortId(finding.fingerprint, 32)}</p>
              </td>
              <td className="px-4 py-4">
                <Badge tone={toneForSeverity(finding.severity)}>{finding.severity}</Badge>
              </td>
              <td className="px-4 py-4 text-slate-300">
                {finding.drift_type} · {finding.resource_type}
              </td>
              <td className="px-4 py-4 font-mono text-xs text-slate-400">{finding.path || "/"}</td>
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

function ReportsTable({
  reports,
  selectedReportId,
  setSelectedReportId,
  onExecute,
  onPlan
}: {
  reports: DriftReport[];
  selectedReportId: string | null;
  setSelectedReportId: (reportId: string) => void;
  onExecute: (reportId: string | null) => void;
  onPlan: (reportId: string | null) => void;
}) {
  if (!reports.length) {
    return <EmptyState message="No drift reports yet. Run a scan to populate report history." />;
  }
  return (
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
                  <Button onClick={() => setSelectedReportId(report.id)} variant="ghost">
                    {report.id === selectedReportId ? "Selected" : "Select"}
                  </Button>
                  <Button onClick={() => onPlan(report.id)}>Plan</Button>
                  <Button onClick={() => onExecute(report.id)} variant="warning">
                    Execute approved
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RemediationTable({
  actions,
  reports,
  onApprove,
  onExecute
}: {
  actions: RemediationAction[];
  reports: DriftReport[];
  onApprove: (actionId: string) => void;
  onExecute: (reportId: string | null) => void;
}) {
  if (!actions.length) {
    return <EmptyState message="No remediation plan yet. Plan remediation from a drift report first." />;
  }
  return (
    <div className="grid gap-3">
      {actions.map((action) => {
        const reportId = reportForAction(action, reports);
        const isApproved = ["approved", "skipped", "succeeded"].includes(action.status);
        return (
          <div
            className="grid gap-4 rounded-2xl border border-white/5 bg-black/20 p-4 lg:grid-cols-[1fr_auto]"
            key={action.id}
          >
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={toneForStatus(action.status)}>{action.status}</Badge>
                <span className="text-sm font-semibold text-white">{action.strategy}</span>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-300">{action.description}</p>
              <p className="mt-2 text-xs text-slate-400">
                Risk {Math.round(action.risk_score)} · Dry run {action.dry_run ? "enabled" : "off"} ·
                Approval {action.requires_approval ? "required" : "automatic"}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button disabled={isApproved} onClick={() => onApprove(action.id)}>
                Approve action
              </Button>
              <Button onClick={() => onExecute(reportId)} variant="warning">
                Execute approved
              </Button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function BaselinesTable({ baselines }: { baselines: Baseline[] }) {
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
                <p className="mt-1 font-mono text-xs text-slate-500">{shortId(baseline.id, 24)}</p>
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

function JobsTable({
  jobs,
  onRunJob
}: {
  jobs: ScheduledJob[];
  onRunJob: (jobId: string) => void;
}) {
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
                <Button onClick={() => onRunJob(job.id)}>Run now</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function IntegrationsGrid({ data }: { data: DashboardData }) {
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

function AuditList({ data }: { data: DashboardData }) {
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

export default App;
