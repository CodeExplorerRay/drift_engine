import type { PropsWithChildren } from "react";

import type { Baseline } from "../../types";
import { Button } from "../Button";
import { Card, SectionHeader } from "../Card";

type QuickActionsProps = {
  baselineName: string;
  baselineVersion: string;
  baselines: Baseline[];
  collectorText: string;
  jobInterval: string;
  jobName: string;
  kubernetesStatus: string;
  loading: boolean;
  namespaces: string;
  scanAutoRemediate: boolean;
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
  onPlan: () => void;
  onRunScan: () => void;
  onScanAutoRemediateChange: (value: boolean) => void;
};

export function QuickActions({
  baselineName,
  baselineVersion,
  baselines,
  collectorText,
  jobInterval,
  jobName,
  kubernetesStatus,
  loading,
  namespaces,
  scanAutoRemediate,
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
  onPlan,
  onRunScan,
  onScanAutoRemediateChange
}: QuickActionsProps) {
  return (
    <Card className="xl:sticky xl:top-24">
      <SectionHeader
        eyebrow="Quick actions"
        title="Operator commands"
        description="Bias toward safe planning, approval, and repeatable scan workflows."
      />
      <div className="space-y-5 p-5">
        <ActionBlock title="Scan">
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
          <Button disabled={loading || baselines.length === 0} onClick={onRunScan} variant="primary">
            Run scan
          </Button>
        </ActionBlock>

        <ActionBlock title="Baseline">
          <Input label="Name" onChange={onBaselineNameChange} value={baselineName} />
          <Input label="Version" onChange={onBaselineVersionChange} value={baselineVersion} />
          <Button disabled={loading} onClick={onCaptureBaseline}>
            Capture baseline
          </Button>
        </ActionBlock>

        <ActionBlock title="Remediation">
          <div className="grid grid-cols-2 gap-2">
            <Button disabled={loading} onClick={onPlan}>
              Plan
            </Button>
            <Button disabled={loading} onClick={onExecute} variant="warning">
              Execute approved
            </Button>
          </div>
        </ActionBlock>

        <ActionBlock title="Kubernetes">
          <Input label="Namespaces" onChange={onNamespacesChange} value={namespaces} />
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs leading-5 text-slate-400">{kubernetesStatus}</p>
            <Button disabled={loading} onClick={onCheckKubernetes}>
              Check
            </Button>
          </div>
        </ActionBlock>

        <ActionBlock title="Schedule">
          <Input label="Job name" onChange={onJobNameChange} value={jobName} />
          <Input label="Interval seconds" onChange={onJobIntervalChange} value={jobInterval} />
          <Button disabled={loading || baselines.length === 0} onClick={onCreateJob}>
            Create job
          </Button>
        </ActionBlock>
      </div>
    </Card>
  );
}

type ActionBlockProps = PropsWithChildren<{
  title: string;
}>;

function ActionBlock({ children, title }: ActionBlockProps) {
  return (
    <div className="rounded-2xl border border-white/5 bg-black/20 p-4">
      <h3 className="text-sm font-semibold text-white">{title}</h3>
      <div className="mt-3 space-y-3">{children}</div>
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
