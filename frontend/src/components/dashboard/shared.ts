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

export function findingTotal(report: DriftReport | null): number {
  if (!report) {
    return 0;
  }
  return report.summary.total ?? report.findings.length;
}
