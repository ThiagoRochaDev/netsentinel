import ReactECharts from "echarts-for-react";
import { baseAxisStyle, chartColors } from "./chartTheme";

export interface CategoryDatum {
  label: string;
  value: number;
}

interface CategoryBarChartProps {
  data: CategoryDatum[];
  colorIndex?: number;
  height?: number;
  valueFormatter?: (v: number) => string;
}

export function CategoryBarChart({ data, colorIndex = 0, height = 260, valueFormatter }: CategoryBarChartProps) {
  const color = chartColors.series[colorIndex % chartColors.series.length];
  const sorted = [...data].sort((a, b) => a.value - b.value);

  const option = {
    grid: { left: 140, right: 40, top: 12, bottom: 12 },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: chartColors.surface1,
      borderColor: chartColors.gridline,
      textStyle: { color: "#fff", fontSize: 12 },
      formatter: (params: unknown) => {
        const p = (params as { name: string; value: number }[])[0];
        return `${p.name}: ${valueFormatter ? valueFormatter(p.value) : p.value}`;
      },
    },
    xAxis: {
      type: "value",
      ...baseAxisStyle,
      axisLine: { show: false },
      axisLabel: { ...baseAxisStyle.axisLabel, formatter: valueFormatter },
    },
    yAxis: {
      type: "category",
      data: sorted.map((d) => d.label),
      axisLine: { lineStyle: { color: chartColors.baseline } },
      axisLabel: { color: chartColors.textSecondary, fontSize: 12 },
      splitLine: { show: false },
    },
    series: [
      {
        type: "bar",
        data: sorted.map((d) => d.value),
        barMaxWidth: 20,
        itemStyle: { color, borderRadius: [0, 4, 4, 0] },
      },
    ],
  };

  return <ReactECharts option={option} style={{ height, width: "100%" }} notMerge />;
}
