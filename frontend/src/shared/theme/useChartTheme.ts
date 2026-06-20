"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export interface ChartTheme {
  grid: string;
  axis: string;
  tooltipBg: string;
  tooltipBorder: string;
  tooltipText: string;
  bar: string;
  line: string;
  pie: string[];
}

const LIGHT_CHART: ChartTheme = {
  grid: "#e2e8f0",
  axis: "#64748b",
  tooltipBg: "#ffffff",
  tooltipBorder: "#e2e8f0",
  tooltipText: "#0f172a",
  bar: "#2563eb",
  line: "#059669",
  pie: ["#2563eb", "#059669", "#dc2626", "#d97706", "#7c3aed", "#64748b"],
};

const DARK_CHART: ChartTheme = {
  grid: "#475569",
  axis: "#94a3b8",
  tooltipBg: "#1e293b",
  tooltipBorder: "#475569",
  tooltipText: "#f8fafc",
  bar: "#3b82f6",
  line: "#34d399",
  pie: ["#3b82f6", "#34d399", "#f87171", "#fbbf24", "#a78bfa", "#94a3b8"],
};

export function useChartTheme(): ChartTheme {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || resolvedTheme !== "dark") {
    return LIGHT_CHART;
  }

  return DARK_CHART;
}
