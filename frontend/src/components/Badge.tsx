export type BadgeTone = "neutral" | "good" | "warning" | "danger" | "info";

const tones: Record<BadgeTone, string> = {
  neutral: "bg-slate-100 text-slate-600 ring-slate-200",
  good: "bg-emerald-50 text-emerald-700 ring-emerald-100",
  warning: "bg-amber-50 text-amber-700 ring-amber-100",
  danger: "bg-red-50 text-red-700 ring-red-100",
  info: "bg-sky-50 text-sky-700 ring-sky-100"
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
