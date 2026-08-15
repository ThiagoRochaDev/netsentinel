import ReactECharts from "echarts-for-react";
import { baseAxisStyle, baseGrid, chartColors } from "./chartTheme";

export interface TimeSeriesPoint {
  t: string;
  v: number;
}

interface TimeSeriesChartProps {
  points: TimeSeriesPoint[];
  seriesName: string;
  colorIndex?: number;
  height?: number;
  area?: boolean;
}

export function TimeSeriesChart({ points, seriesName, colorIndex = 0, height = 220, area = true }: TimeSeriesChartProps) {
  const color = chartColors.series[colorIndex % chartColors.series.length];

  const option = {
    grid: baseGrid,
    tooltip: {
      trigger: "axis",
      backgroundColor: chartColors.surface1,
      borderColor: chartColors.gridline,
      textStyle: { color: "#fff", fontSize: 12 },
      axisPointer: { type: "cross", lineStyle: { color: chartColors.baseline } },
    },
    xAxis: {
      type: "category",
      data: points.map((p) => p.t),
      ...baseAxisStyle,
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      ...baseAxisStyle,
      axisLine: { show: false },
    },
    series: [
      {
        name: seriesName,
        type: "line",
        data: points.map((p) => p.v),
        showSymbol: false,
        lineStyle: { width: 2, color },
        itemStyle: { color },
        areaStyle: area ? { color, opacity: 0.1 } : undefined,
        smooth: false,
      },
    ],
  };

  return <ReactECharts option={option} style={{ height, width: "100%" }} notMerge />;
}
