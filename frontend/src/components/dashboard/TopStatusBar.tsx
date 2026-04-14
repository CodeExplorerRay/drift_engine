import { Badge, toneForStatus } from "../Badge";
import { Button } from "../Button";
import { relativeTime } from "./shared";

type TopStatusBarProps = {
  environment: string | null;
  health: string;
  lastScan: string | null;
  loading: boolean;
  onRefresh: () => void;
  onRunScan: () => void;
  posture: string;
  riskScore: number | null;
};

export function TopStatusBar({
  environment,
  health,
  lastScan,
  loading,
  onRefresh,
  onRunScan,
  posture,
  riskScore
}: TopStatusBarProps) {
  const postureTone =
    posture === "Critical" ? "danger" : posture === "Warning" ? "warning" : posture === "Stable" ? "good" : "info";

  return (
    <header className="sticky top-0 z-20 -mx-4 mb-6 border-b border-white/5 bg-[#0b0f14]/90 px-4 py-4 backdrop-blur sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">
      <div className="mx-auto flex max-w-[1480px] flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Posture
          </p>
          <div className="mt-1 flex flex-wrap items-center gap-3">
            <p className="text-xl font-semibold tracking-[-0.03em] text-white">Operator Dashboard</p>
            <Badge tone={postureTone}>{posture}</Badge>
          </div>
          <p className="mt-2 text-sm text-slate-400">
            {(environment || "current environment").toUpperCase()} ·{" "}
            {riskScore === null ? "No report selected" : `Risk ${riskScore}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone={toneForStatus(health)}>{health}</Badge>
          <span className="hidden text-sm text-slate-400 xl:inline">
            Last scan {relativeTime(lastScan)}
          </span>
          <a
            className="rounded-xl border border-white/10 bg-white/5 px-3.5 py-2 text-sm font-semibold text-slate-200 hover:border-white/20 hover:bg-white/10"
            href="/docs"
          >
            API docs
          </a>
          <Button disabled={loading} onClick={onRefresh} variant="ghost">
            {loading ? "Refreshing" : "Refresh"}
          </Button>
          <Button disabled={loading} onClick={onRunScan} variant="primary">
            Run Scan
          </Button>
        </div>
      </div>
    </header>
  );
}
