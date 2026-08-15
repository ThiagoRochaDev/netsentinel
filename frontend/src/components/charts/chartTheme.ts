// ECharts needs resolved color strings, not CSS custom properties — this
// reads the tokens once from :root so charts stay in sync with theme.css.
function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export const chartColors = {
  series: [
    cssVar("--series-1"),
    cssVar("--series-2"),
    cssVar("--series-3"),
    cssVar("--series-4"),
    cssVar("--series-5"),
    cssVar("--series-6"),
    cssVar("--series-7"),
    cssVar("--series-8"),
  ],
  gridline: cssVar("--gridline"),
  baseline: cssVar("--baseline"),
  textMuted: cssVar("--text-muted"),
  textSecondary: cssVar("--text-secondary"),
  surface1: cssVar("--surface-1"),
  status: {
    good: cssVar("--status-good"),
    warning: cssVar("--status-warning"),
    serious: cssVar("--status-serious"),
    critical: cssVar("--status-critical"),
  },
};

export const baseGrid = { left: 48, right: 20, top: 24, bottom: 32 };

export const baseAxisStyle = {
  axisLine: { lineStyle: { color: chartColors.baseline } },
  axisLabel: { color: chartColors.textMuted, fontSize: 11 },
  splitLine: { lineStyle: { color: chartColors.gridline, type: "solid" as const } },
};
