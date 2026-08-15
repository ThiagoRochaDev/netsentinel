import type { Severity } from "../api/client";

const SEVERITY_LABEL: Record<Severity, string> = {
  critical: "Crítico",
  high: "Alto",
  medium: "Médio",
  low: "Baixo",
  info: "Info",
};

const SEVERITY_COLOR: Record<Severity, string> = {
  critical: "var(--status-critical)",
  high: "var(--status-serious)",
  medium: "var(--status-warning)",
  low: "var(--series-1)",
  info: "var(--text-muted)",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  const color = SEVERITY_COLOR[severity] ?? "var(--text-muted)";
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        color,
        fontSize: 12,
        fontWeight: 600,
      }}
    >
      <span style={{ width: 8, height: 8, borderRadius: "50%", background: color, display: "inline-block" }} />
      {SEVERITY_LABEL[severity] ?? severity}
    </span>
  );
}
