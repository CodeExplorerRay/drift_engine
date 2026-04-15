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
import { Badge } from "./components/Badge";
import { Card } from "./components/Card";
import { IncidentSpotlight } from "./components/dashboard/IncidentSpotlight";
import { PostureSummary } from "./components/dashboard/PostureSummary";
import { PriorityQueue } from "./components/dashboard/PriorityQueue";
import { QuickActions } from "./components/dashboard/QuickActions";
import {
  AuditList,
  BaselinesTable,
  FindingsTable,
  IntegrationsGrid,
  JobsTable,
  RemediationTable,
  ReportsTable
} from "./components/dashboard/Tables";
import { TopStatusBar } from "./components/dashboard/TopStatusBar";
import { findingTotal, formatTime, relativeTime, shortId } from "./components/dashboard/shared";
import type {
  DashboardData,
  DashboardSection,
  DriftFinding,
  DriftReport,
  Integration,
  RemediationCapability
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
const INITIAL_LOADED_AT = new Date(0).toISOString();

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
  audit: [],
  remediationCapability: {
    enabled: false,
    dry_run: true,
    executor_mode: "unknown",
    real_execution_available: false,
    simulation_only: true,
    can_execute: false
  },
  errors: {},
  loaded_at: INITIAL_LOADED_AT
};

function splitCsv(value: string): string[] | null {
  const items = value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  return items.length ? items : null;
}

function isSevere(finding: DriftFinding): boolean {
  return finding.trusted !== false && ["critical", "high"].includes(finding.severity.toLowerCase());
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

function describeSidebarStatus({
  activityNotice,
  baselines,
  errors,
  hasLoadedDashboard,
  latestReport,
  loading,
  partialScan
}: {
  activityNotice: string | null;
  baselines: number;
  errors: number;
  hasLoadedDashboard: boolean;
  latestReport: DriftReport | null;
  loading: boolean;
  partialScan: boolean;
}): { detail: string; headline: string } {
  if (loading && !hasLoadedDashboard) {
    return {
      headline: "Awaiting first API response",
      detail: "The console has not received live baselines, reports, or integrations yet."
    };
  }
  if (loading) {
    return {
      headline: "Refreshing live data",
      detail: "Previously loaded data is still visible while the next refresh completes."
    };
  }
  if (errors > 0) {
    return {
      headline: "Dashboard data is degraded",
      detail: `${errors} section${errors === 1 ? "" : "s"} failed to load. Empty tables may not mean clean state.`
    };
  }
  if (partialScan && latestReport) {
    return {
      headline: "Latest scan is partial",
      detail:
        latestReport.integrity_warnings[0] ??
        "Collector failures mean the selected report is not fully authoritative."
    };
  }
  if (latestReport) {
    return {
      headline: "Latest scan is ready",
      detail: activityNotice ?? `Report ${shortId(latestReport.id, 16)} is available for review.`
    };
  }
  if (baselines > 0) {
    return {
      headline: "Ready to run a scan",
      detail: activityNotice ?? "A baseline exists. Run drift detection to compare live state."
    };
  }
  return {
    headline: "No baseline captured yet",
    detail: activityNotice ?? "Capture current state before the console can produce drift evidence."
  };
}

function scanIsPartial(report: DriftReport | null): boolean {
  return report?.scan_completeness === "partial";
}

function errorFor(
  errors: Partial<Record<DashboardSection, string>>,
  ...sections: DashboardSection[]
): string | null {
  for (const section of sections) {
    if (errors[section]) {
      return errors[section] ?? null;
    }
  }
  return null;
}

function selectMostUrgentFinding(report: DriftReport | null): DriftFinding | null {
  if (!report || report.findings.length === 0) {
    return null;
  }
  const trustedFindings = report.findings.filter((finding) => finding.trusted !== false);
  if (!trustedFindings.length) {
    return null;
  }
  return [...trustedFindings].sort((left, right) => right.risk_score - left.risk_score)[0];
}

function firstReason(...reasons: Array<string | null>): string | null {
  return reasons.find((reason): reason is string => Boolean(reason)) ?? null;
}

function scrollToDashboardSection(sectionId: string) {
  if (typeof window === "undefined") {
    return;
  }
  window.requestAnimationFrame(() => {
    document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function App() {
  const [data, setData] = useState<DashboardData>(initialData);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("findings");
  const [highlightEvidence, setHighlightEvidence] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activityNotice, setActivityNotice] = useState<string | null>(null);
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
  const dashboardErrors = Object.entries(data.errors);
  const partialScan = scanIsPartial(selectedReport);
  const selectedBaselineId = selectedReport?.baseline_id ?? data.baselines[0]?.id ?? null;
  const trimmedBaselineName = baselineName.trim();
  const trimmedBaselineVersion = baselineVersion.trim() || "1.0.0";
  const trimmedJobName = jobName.trim();
  const collectorNames = splitCsv(collectorText);
  const hasValidCollectorSelection = (collectorNames?.length ?? 0) <= 20;
  const parsedJobInterval = Number(jobInterval.trim());
  const hasValidJobInterval = Number.isInteger(parsedJobInterval) && parsedJobInterval >= 1;
  const loadingDisabledReason = loading ? "Wait for the current dashboard action to finish." : null;
  const collectorLimitReason = !hasValidCollectorSelection ? "Use 20 collectors or fewer per request." : null;
  const baselineRequiredReason = !selectedBaselineId ? "Capture a baseline first." : null;
  const reportRequiredReason = !selectedReport?.id ? "Run or select a report first." : null;
  const executorUnavailableReason = !data.remediationCapability.can_execute
    ? "Current executor cannot execute approved remediation."
    : null;
  const runScanDisabledReason = firstReason(
    loadingDisabledReason,
    baselineRequiredReason,
    collectorLimitReason
  );
  const captureBaselineDisabledReason = firstReason(
    loadingDisabledReason,
    !trimmedBaselineName ? "Enter a baseline name." : null,
    collectorLimitReason
  );
  const createJobDisabledReason = firstReason(
    loadingDisabledReason,
    baselineRequiredReason,
    !trimmedJobName ? "Enter a job name." : null,
    collectorLimitReason,
    !hasValidJobInterval ? "Enter a whole-number interval in seconds." : null
  );
  const planRemediationDisabledReason = firstReason(loadingDisabledReason, reportRequiredReason);
  const executeRemediationDisabledReason = firstReason(
    loadingDisabledReason,
    reportRequiredReason,
    executorUnavailableReason
  );
  const canCaptureBaseline = !loading && trimmedBaselineName.length > 0 && hasValidCollectorSelection;
  const canRunScan = !loading && Boolean(selectedBaselineId) && hasValidCollectorSelection;
  const canCreateJob =
    !loading &&
    Boolean(selectedBaselineId) &&
    trimmedJobName.length > 0 &&
    hasValidCollectorSelection &&
    hasValidJobInterval;
  const canPlanRemediation = !loading && Boolean(selectedReport?.id);
  const canExecuteRemediation =
    !loading && Boolean(selectedReport?.id) && data.remediationCapability.can_execute;
  const remediationActionHint =
    !canPlanRemediation && planRemediationDisabledReason
      ? planRemediationDisabledReason
      : !canExecuteRemediation && executeRemediationDisabledReason
        ? canPlanRemediation
          ? `Planning is available, but execution is blocked. ${executeRemediationDisabledReason}`
          : executeRemediationDisabledReason
        : null;
  const executionLabel = data.remediationCapability.simulation_only
    ? "Simulate execution"
    : "Execute approved";
  const posture =
    criticalFindings > 0
      ? "Critical"
      : pendingApprovals.length > 0 ||
          unhealthyIntegrations.length > 0 ||
          overdueJobs.length > 0 ||
          partialScan ||
          dashboardErrors.length > 0
        ? "Warning"
        : latestReport
          ? "Stable"
          : "Awaiting scan";
  const environment = data.health.details?.environment ?? null;
  const riskScore = selectedReport ? Math.round(selectedReport.risk_score) : null;
  const tabCounts = countTabs(data, selectedReport);
  const hasLoadedDashboard = data.loaded_at !== INITIAL_LOADED_AT;
  const sidebarStatus = describeSidebarStatus({
    activityNotice,
    baselines: data.baselines.length,
    errors: dashboardErrors.length,
    hasLoadedDashboard,
    latestReport,
    loading,
    partialScan
  });

  async function refresh(quiet = false) {
    setLoading(true);
    try {
      const dashboard = await loadDashboard();
      setData(dashboard);
      if (!selectedReportId && dashboard.reports[0]) {
        setSelectedReportId(dashboard.reports[0].id);
      }
      if (!quiet) {
        setActivityNotice("Dashboard refreshed");
      }
    } catch (error) {
      setActivityNotice(error instanceof Error ? error.message : "Dashboard refresh failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh(true);
  }, []);

  useEffect(() => {
    if (!highlightEvidence) {
      return;
    }
    const timeoutId = window.setTimeout(() => {
      setHighlightEvidence(false);
    }, 1400);
    return () => window.clearTimeout(timeoutId);
  }, [highlightEvidence]);

  async function perform(message: string, task: () => Promise<unknown>) {
    setLoading(true);
    try {
      await task();
      setActivityNotice(message);
      await refresh(true);
    } catch (error) {
      setActivityNotice(error instanceof Error ? error.message : "Action failed");
    } finally {
      setLoading(false);
    }
  }

  async function onCaptureBaseline() {
    if (!trimmedBaselineName) {
      setActivityNotice("Baseline name is required");
      return;
    }
    if (!hasValidCollectorSelection) {
      setActivityNotice("Select 20 collectors or fewer per request");
      return;
    }
    await perform("Baseline captured", async () => {
      await captureBaseline({
        name: trimmedBaselineName,
        version: trimmedBaselineVersion,
        collector_names: collectorNames
      });
    });
  }

  async function onRunScan() {
    if (!selectedBaselineId) {
      setActivityNotice("Create a baseline before running a scan");
      return;
    }
    if (!hasValidCollectorSelection) {
      setActivityNotice("Select 20 collectors or fewer per request");
      return;
    }
    await perform("Drift scan completed", async () => {
      const report = await runDriftScan({
        baseline_id: selectedBaselineId,
        collector_names: collectorNames,
        auto_remediate: scanAutoRemediate
      });
      setSelectedReportId(report.id);
      setActiveTab("findings");
    });
  }

  async function onCreateJob() {
    if (!selectedBaselineId) {
      setActivityNotice("Create a baseline before scheduling a job");
      return;
    }
    if (!trimmedJobName) {
      setActivityNotice("Job name is required");
      return;
    }
    if (!hasValidCollectorSelection) {
      setActivityNotice("Select 20 collectors or fewer per request");
      return;
    }
    if (!hasValidJobInterval) {
      setActivityNotice("Interval seconds must be a positive whole number");
      return;
    }
    await perform("Scheduled job created", async () => {
      await createJob({
        name: trimmedJobName,
        baseline_id: selectedBaselineId,
        interval_seconds: parsedJobInterval,
        collector_names: collectorNames
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
      setActivityNotice("Kubernetes readiness checked");
    } catch (error) {
      setActivityNotice(error instanceof Error ? error.message : "Kubernetes check failed");
    } finally {
      setLoading(false);
    }
  }

  async function onPlanRemediation(reportId: string | null) {
    if (!reportId) {
      setActivityNotice("Select a report before planning remediation");
      return;
    }
    await perform("Remediation plan prepared", async () => {
      await planRemediation(reportId);
      setActiveTab("remediation");
    });
  }

  async function onExecuteRemediation(reportId: string | null) {
    if (!reportId) {
      setActivityNotice("Select a report before executing remediation");
      return;
    }
    if (!data.remediationCapability.can_execute) {
      setActivityNotice("Remediation execution is not available with the current executor");
      return;
    }
    await perform(
      data.remediationCapability.simulation_only
        ? "Remediation simulation completed"
        : "Approved remediation executed",
      async () => {
        await executeRemediation(reportId);
        setActiveTab("remediation");
      }
    );
  }

  function openEvidenceTab(tab: Tab) {
    setActiveTab(tab);
    setHighlightEvidence(false);
    window.requestAnimationFrame(() => {
      setHighlightEvidence(true);
    });
    scrollToDashboardSection("evidence-tabs");
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
            <p className="mt-2 text-sm font-semibold text-white">{sidebarStatus.headline}</p>
            <p className="mt-2 text-xs leading-5 text-slate-400">{sidebarStatus.detail}</p>
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
            runScanDisabledReason={runScanDisabledReason}
            environment={environment}
            health={data.health.status}
            lastScan={latestReport?.generated_at ?? null}
            loading={loading}
            partialScan={partialScan}
            canRunScan={canRunScan}
            onRefresh={() => refresh()}
            onRunScan={onRunScan}
            posture={posture}
            riskScore={riskScore}
          />

          <div className="mx-auto max-w-[1480px] space-y-6" id="overview">
            {dashboardErrors.length || partialScan ? (
              <DashboardIntegrityBanner
                errors={data.errors}
                partialReport={partialScan ? selectedReport : null}
              />
            ) : null}

            <PostureSummary
              criticalFindings={criticalFindings}
              enabledIntegrations={enabledIntegrations.length}
              overdueJobs={overdueJobs.length}
              pendingApprovals={pendingApprovals.length}
              scheduledJobs={data.jobs.length}
              unhealthyIntegrations={unhealthyIntegrations.length}
            />

            <section className="space-y-6">
              <IncidentSpotlight
                environment={environment}
                finding={urgentFinding}
                onOpenFindings={() => openEvidenceTab("findings")}
                report={selectedReport}
                onPlan={() => onPlanRemediation(selectedReport?.id ?? null)}
              />

              <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_370px]">
                <PriorityQueue
                  criticalFindings={criticalFindings}
                  finding={urgentFinding}
                  integrations={unhealthyIntegrations}
                  jobs={overdueJobs}
                  pendingApprovals={pendingApprovals}
                  report={selectedReport}
                  onOpenFindings={() => openEvidenceTab("findings")}
                  onOpenIntegrations={() => openEvidenceTab("integrations")}
                  onOpenJobs={() => openEvidenceTab("jobs")}
                  onOpenRemediation={() => openEvidenceTab("remediation")}
                />

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
                  remediationCapability={data.remediationCapability}
                  canCaptureBaseline={canCaptureBaseline}
                  canCreateJob={canCreateJob}
                  canExecute={canExecuteRemediation}
                  canPlan={canPlanRemediation}
                  canRunScan={canRunScan}
                  captureBaselineDisabledReason={captureBaselineDisabledReason}
                  createJobDisabledReason={createJobDisabledReason}
                  remediationDisabledReason={remediationActionHint}
                  runScanDisabledReason={runScanDisabledReason}
                  scanAutoRemediate={scanAutoRemediate}
                  executionLabel={executionLabel}
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
                  onOpenRemediation={() => openEvidenceTab("remediation")}
                  onPlan={() => onPlanRemediation(selectedReport?.id ?? null)}
                  onRunScan={onRunScan}
                  onScanAutoRemediateChange={setScanAutoRemediate}
                />
              </div>
            </section>

            <EvidenceTabs
              activeTab={activeTab}
              data={data}
              errors={data.errors}
              executeDisabledReason={!loading ? executeRemediationDisabledReason : null}
              executionLabel={executionLabel}
              highlightEvidence={highlightEvidence}
              loading={loading}
              remediationCapability={data.remediationCapability}
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

function DashboardIntegrityBanner({
  errors,
  partialReport
}: {
  errors: Partial<Record<DashboardSection, string>>;
  partialReport: DriftReport | null;
}) {
  const entries = Object.entries(errors).filter(
    (entry): entry is [DashboardSection, string] => typeof entry[1] === "string"
  );
  return (
    <Card className="border-amber-400/20 bg-amber-950/20 p-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Badge tone="warning">Dashboard degraded</Badge>
          <p className="mt-3 text-sm font-semibold text-white">
            Some data is incomplete or failed to load.
          </p>
          <p className="mt-1 text-sm leading-6 text-slate-400">
            Empty sections below may mean an API failure, not a clean system state.
          </p>
        </div>
        {partialReport ? (
          <Badge tone="warning">{`Partial scan ${shortId(partialReport.id, 16)}`}</Badge>
        ) : null}
      </div>
      {entries.length ? (
        <div className="mt-4 grid gap-2 md:grid-cols-2">
          {entries.map(([section, message]) => (
            <div className="rounded-xl border border-white/5 bg-black/20 px-3 py-2" key={section}>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-amber-200">
                {section}
              </p>
              <p className="mt-1 text-xs leading-5 text-slate-400">{message}</p>
            </div>
          ))}
        </div>
      ) : null}
      {partialReport?.integrity_warnings.length ? (
        <p className="mt-3 text-xs leading-5 text-amber-100/80">
          {partialReport.integrity_warnings.join(" ")}
        </p>
      ) : null}
    </Card>
  );
}

function EvidenceTabs({
  activeTab,
  data,
  errors,
  executeDisabledReason,
  executionLabel,
  highlightEvidence,
  loading,
  remediationCapability,
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
  errors: Partial<Record<DashboardSection, string>>;
  executeDisabledReason: string | null;
  executionLabel: string;
  highlightEvidence: boolean;
  loading: boolean;
  remediationCapability: RemediationCapability;
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
    <Card
      className={[
        "overflow-hidden scroll-mt-28",
        highlightEvidence ? "evidence-panel-highlight" : ""
      ].join(" ")}
      id="evidence-tabs"
    >
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
            {selectedReport?.scan_completeness === "partial" ? (
              <Badge tone="warning">Partial scan</Badge>
            ) : null}
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
        {activeTab === "findings" ? (
          <FindingsTable error={errorFor(errors, "reports")} report={selectedReport} />
        ) : null}
        {activeTab === "reports" ? (
          <ReportsTable
            error={errorFor(errors, "reports")}
            executeDisabledReason={executeDisabledReason}
            executionLabel={executionLabel}
            canExecuteRemediation={remediationCapability.can_execute}
            loading={loading}
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
            canExecuteRemediation={remediationCapability.can_execute}
            error={errorFor(errors, "actions", "remediationCapability")}
            executionLabel={executionLabel}
            loading={loading}
            remediationCapability={remediationCapability}
            reports={data.reports}
            onApprove={onApprove}
            onExecute={onExecute}
          />
        ) : null}
        {activeTab === "baselines" ? (
          <BaselinesTable baselines={data.baselines} error={errorFor(errors, "baselines")} />
        ) : null}
        {activeTab === "jobs" ? (
          <JobsTable error={errorFor(errors, "jobs")} jobs={data.jobs} loading={loading} onRunJob={onRunJob} />
        ) : null}
        {activeTab === "integrations" ? (
          <IntegrationsGrid data={data} error={errorFor(errors, "integrations")} />
        ) : null}
        {activeTab === "audit" ? <AuditList data={data} error={errorFor(errors, "audit")} /> : null}
      </div>
    </Card>
  );
}

export default App;
