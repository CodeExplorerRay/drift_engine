import { useState, type PropsWithChildren, type ReactNode } from "react";

import type { Baseline, RemediationCapability } from "../../types";
import { Button } from "../Button";
import { Card, SectionHeader } from "../Card";

type QuickActionsProps = {
  baselineName: string;
  baselineVersion: string;
  baselines: Baseline[];
  canCaptureBaseline: boolean;
  canCreateJob: boolean;
  canExecute: boolean;
  canPlan: boolean;
  canRunScan: boolean;
  captureBaselineDisabledReason: string | null;
  collectorText: string;
  createJobDisabledReason: string | null;
  jobInterval: string;
  jobName: string;
  kubernetesStatus: string;
  loading: boolean;
  namespaces: string;
  pendingApprovals: number;
  remediationDisabledReason: string | null;
  remediationCapability: RemediationCapability;
  runScanDisabledReason: string | null;
  scanAutoRemediate: boolean;
  executionLabel: string;
  onBaselineNameChange: (value: string) => void;
  onBaselineVersionChange: (value: string) => void;
  onCaptureBaseline: () => void;
  onCheckKubernetes: () => void;
  onCollectorTextChange: (value: string) => void;
  onCreateJob: () => void;
  onExecute: () => void;
  onJobIntervalChange: (value: string) => void;
  onJobNameChange: (value: string) => void;
  onNamespacesChange: (value: string) => void;
  onOpenRemediation: () => void;
  onPlan: () => void;
  onRunScan: () => void;
  onScanAutoRemediateChange: (value: boolean) => void;
};

export function QuickActions({
  baselineName,
  baselineVersion,
  baselines,
  canCaptureBaseline,
  canCreateJob,
  canExecute,
  canPlan,
  canRunScan,
  captureBaselineDisabledReason,
  collectorText,
  createJobDisabledReason,
  jobInterval,
  jobName,
  kubernetesStatus,
  loading,
  namespaces,
  pendingApprovals,
  remediationDisabledReason,
  remediationCapability,
  runScanDisabledReason,
  scanAutoRemediate,
  executionLabel,
  onBaselineNameChange,
  onBaselineVersionChange,
  onCaptureBaseline,
  onCheckKubernetes,
  onCollectorTextChange,
  onCreateJob,
  onExecute,
  onJobIntervalChange,
  onJobNameChange,
  onNamespacesChange,
  onOpenRemediation,
  onPlan,
  onRunScan,
  onScanAutoRemediateChange
}: QuickActionsProps) {
  return (
    <Card className="xl:sticky xl:top-24">
      <SectionHeader
        eyebrow="Quick actions"
        title="Operator commands"
        description="Run the next safe command without leaving the dashboard."
      />
      <div className="space-y-3 p-5">
        <ActionBlock
          actions={
            <Button disabled={!canRunScan} onClick={onRunScan} variant="primary">
              Run scan
            </Button>
          }
          actionHint={!canRunScan ? runScanDisabledReason : null}
          defaultOpen
          description={baselines.length ? `Using ${collectorText}` : "Capture a baseline first"}
          title="Run drift scan"
        >
          <Input
            label="Collectors"
            onChange={onCollectorTextChange}
            placeholder="file,package,kubernetes"
            value={collectorText}
          />
          <label className="flex items-center gap-2 text-sm font-medium text-slate-300">
            <input
              checked={scanAutoRemediate}
              className="h-4 w-4 rounded border-white/10 bg-[#0b0f14] text-sky-400"
              onChange={(event) => onScanAutoRemediateChange(event.target.checked)}
              type="checkbox"
            />
            Auto-remediate after scan
          </label>
        </ActionBlock>

        <ActionBlock
          actions={
            <Button disabled={!canCaptureBaseline} onClick={onCaptureBaseline}>
              Capture baseline
            </Button>
          }
          actionHint={!canCaptureBaseline ? captureBaselineDisabledReason : null}
          description={`${baselines.length} baseline${baselines.length === 1 ? "" : "s"} stored`}
          title="Capture current state"
        >
          <Input label="Name" onChange={onBaselineNameChange} value={baselineName} />
          <Input label="Version" onChange={onBaselineVersionChange} value={baselineVersion} />
        </ActionBlock>

        <ActionBlock
          actions={
            <>
              <Button disabled={!canPlan} onClick={onPlan}>
                Plan
              </Button>
              <Button disabled={!canExecute} onClick={onExecute} variant="warning">
                {executionLabel}
              </Button>
            </>
          }
          actionHint={remediationDisabledReason}
          defaultOpen={pendingApprovals > 0}
          description={
            pendingApprovals
              ? `${pendingApprovals} approval${pendingApprovals === 1 ? "" : "s"} waiting`
              : "No approvals waiting"
          }
          title="Remediation"
        >
          <p className="rounded-xl border border-white/5 bg-black/20 px-3 py-2 text-xs leading-5 text-slate-400">
            Executor {remediationCapability.executor_mode}.{" "}
            {remediationCapability.simulation_only
              ? "Only simulated remediation is available."
              : "Real execution is available."}
          </p>
          <Button className="w-full" disabled={loading} onClick={onOpenRemediation} variant="ghost">
            Open remediation queue
          </Button>
        </ActionBlock>

        <ActionBlock
          actions={
            <Button disabled={loading} onClick={onCheckKubernetes}>
              Check
            </Button>
          }
          description={kubernetesStatus}
          title="Kubernetes readiness"
        >
          <Input
            label="Namespaces"
            onChange={onNamespacesChange}
            placeholder="default,platform"
            value={namespaces}
          />
        </ActionBlock>

        <ActionBlock
          actions={
            <Button disabled={!canCreateJob} onClick={onCreateJob}>
              Create job
            </Button>
          }
          actionHint={!canCreateJob ? createJobDisabledReason : null}
          description="Create a recurring scan from the current inputs"
          title="Schedule scans"
        >
          <Input label="Job name" onChange={onJobNameChange} value={jobName} />
          <Input label="Interval seconds" onChange={onJobIntervalChange} value={jobInterval} />
        </ActionBlock>
      </div>
    </Card>
  );
}

type ActionBlockProps = PropsWithChildren<{
  actionHint?: string | null;
  actions?: ReactNode;
  defaultOpen?: boolean;
  description: string;
  title: string;
}>;

function ActionBlock({
  actionHint,
  actions,
  children,
  defaultOpen = false,
  description,
  title
}: ActionBlockProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
      <button
        aria-expanded={isOpen}
        className="w-full text-left"
        onClick={() => setIsOpen((current) => !current)}
        type="button"
      >
        <span className="flex items-start gap-3">
          <span
            className={[
              "mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full border border-white/10 text-[11px] text-slate-400 transition",
              isOpen ? "rotate-90 bg-white/5 text-white" : "bg-black/20"
            ].join(" ")}
          >
            {">"}
          </span>
          <span className="min-w-0 flex-1">
            <span className="block text-sm font-semibold leading-5 text-white">{title}</span>
            <span className="mt-1 block text-xs leading-5 text-slate-400">{description}</span>
          </span>
        </span>
      </button>
      {isOpen ? (
        <div className="mt-4 space-y-3 border-t border-white/5 pt-4">
          {children}
          {actions || actionHint ? (
            <div className="space-y-2 pt-1">
              {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
              {actionHint ? <p className="text-xs leading-5 text-slate-500">{actionHint}</p> : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

type InputProps = {
  label: string;
  onChange: (value: string) => void;
  placeholder?: string;
  value: string;
};

function Input({ label, onChange, placeholder, value }: InputProps) {
  return (
    <label className="block">
      <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
        {label}
      </span>
      <input
        className="mt-1 h-10 w-full rounded-xl border border-white/10 bg-[#0b0f14] px-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-sky-400 focus:ring-4 focus:ring-sky-500/10"
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        value={value}
      />
    </label>
  );
}
