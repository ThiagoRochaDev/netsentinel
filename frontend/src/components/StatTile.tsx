interface StatTileProps {
  label: string;
  value: string | number;
  accent?: "default" | "critical" | "warning" | "good";
  onClick?: () => void;
}

const ACCENT_COLOR: Record<NonNullable<StatTileProps["accent"]>, string> = {
  default: "var(--text-primary)",
  critical: "var(--status-critical)",
  warning: "var(--status-warning)",
  good: "var(--status-good)",
};

export function StatTile({ label, value, accent = "default", onClick }: StatTileProps) {
  const clickable = Boolean(onClick);
  return (
    <div
      className="card"
      onClick={onClick}
      onKeyDown={
        clickable
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onClick?.();
              }
            }
          : undefined
      }
      role={clickable ? "button" : undefined}
      tabIndex={clickable ? 0 : undefined}
      style={{
        padding: "18px 20px",
        display: "flex",
        flexDirection: "column",
        gap: 6,
        cursor: clickable ? "pointer" : undefined,
        transition: clickable ? "border-color 0.15s ease, background 0.15s ease" : undefined,
      }}
      onMouseEnter={clickable ? (e) => (e.currentTarget.style.borderColor = "var(--series-1)") : undefined}
      onMouseLeave={clickable ? (e) => (e.currentTarget.style.borderColor = "var(--border)") : undefined}
    >
      <div className="text-muted" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: "0.04em" }}>
        {label}
      </div>
      <div style={{ fontSize: 32, fontWeight: 700, color: ACCENT_COLOR[accent], lineHeight: 1 }}>{value}</div>
      {clickable && (
        <div className="text-muted" style={{ fontSize: 11 }}>
          Ver detalhes →
        </div>
      )}
    </div>
  );
}
