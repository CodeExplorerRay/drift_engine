export type BadgeTone = "neutral" | "good" | "warning" | "danger" | "info";

const tones: Record<BadgeTone, string> = {
  neutral: "bg-white/5 text-slate-300 ring-white/10",
  good: "bg-emerald-500/12 text-emerald-300 ring-emerald-400/15",
  warning: "bg-amber-500/12 text-amber-300 ring-amber-400/15",
  danger: "bg-red-500/12 text-red-300 ring-red-400/15",
  info: "bg-sky-500/12 text-sky-300 ring-sky-400/15"
};

export function toneForStatus(status: string | null | undefined): BadgeTone {
  const value = String(status || "").toLowerCase();
  if (["ready", "ok", "passed", "enabled", "approved", "succeeded"].includes(value)) {
    return "good";
  }
  if (["planned", "waiting_approval", "warning", "missing_configuration"].includes(value)) {
    return "warning";
  }
  if (["critical", "failed", "error", "disabled", "not_ready"].includes(value)) {
    return "danger";
  }
  return "info";
}

export function toneForSeverity(severity: string | null | undefined): BadgeTone {
  const value = String(severity || "").toLowerCase();
  if (["critical", "high"].includes(value)) {
    return "danger";
  }
  if (value === "medium") {
    return "warning";
  }
  return "info";
}

export function Badge({ children, tone = "neutral" }: { children: string; tone?: BadgeTone }) {
  return (
    <span
      className={[
        "inline-flex h-6 w-fit items-center rounded-full px-2.5 text-[11px] font-bold uppercase",
        "tracking-[0.08em] ring-1 ring-inset",
        tones[tone]
      ].join(" ")}
    >
      {children}
    </span>
  );
}
