import type { DriftReport } from "../../types";

export function shortId(value: string | null | undefined, length = 12): string {
  if (!value) {
    return "-";
  }
  return value.length > length ? `${value.slice(0, length)}...` : value;
}

export function formatTime(value: string | null | undefined): string {
  if (!value) {
    return "Never";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

export function relativeTime(value: string | null | undefined): string {
  if (!value) {
    return "Never";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const diffMs = date.getTime() - Date.now();
  const absMs = Math.abs(diffMs);
  const units = [
    { unit: "day", ms: 86_400_000 },
    { unit: "hour", ms: 3_600_000 },
    { unit: "minute", ms: 60_000 }
  ] as const;

  if (absMs < 45_000) {
    return "just now";
  }

  const formatter = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
  for (const { unit, ms } of units) {
    if (absMs >= ms) {
      return formatter.format(Math.round(diffMs / ms), unit);
    }
  }

  return formatter.format(Math.round(diffMs / 1000), "second");
}

export function humanizeLabel(value: string | null | undefined): string {
  if (!value) {
    return "Unknown";
  }
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function findingTotal(report: DriftReport | null): number {
  if (!report) {
    return 0;
  }
  return report.summary.total ?? report.findings.length;
}
