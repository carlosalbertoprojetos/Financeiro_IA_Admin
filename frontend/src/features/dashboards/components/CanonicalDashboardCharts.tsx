"use client";

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { CanonicalDashboardResponse } from "../types";
import { useChartTheme } from "@/shared/theme/useChartTheme";
import { Card } from "@/shared/ui";

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold text-foreground">{title}</h3>
      <div className="h-72">{children}</div>
    </Card>
  );
}

function formatDayLabel(isoDate: string): string {
  try {
    return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short" }).format(
      new Date(isoDate),
    );
  } catch {
    return isoDate;
  }
}

interface CanonicalDashboardChartsProps {
  data: CanonicalDashboardResponse | null;
}

export function CanonicalDashboardCharts({ data }: CanonicalDashboardChartsProps) {
  const chartTheme = useChartTheme();

  const tooltipStyle = useMemo(
    () => ({
      backgroundColor: chartTheme.tooltipBg,
      border: `1px solid ${chartTheme.tooltipBorder}`,
      borderRadius: "8px",
      color: chartTheme.tooltipText,
    }),
    [chartTheme],
  );

  if (!data) {
    return (
      <div className="grid gap-4 xl:grid-cols-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-80 animate-pulse rounded-xl bg-surface-muted" />
        ))}
      </div>
    );
  }

  const trendData = data.trend_7d.map((point) => ({
    ...point,
    label: formatDayLabel(point.date),
  }));

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <ChartCard title="Tasks por status">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data.tasks_by_status}>
            <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.grid} />
            <XAxis dataKey="status" tick={{ fontSize: 11, fill: chartTheme.axis }} />
            <YAxis allowDecimals={false} tick={{ fill: chartTheme.axis }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Bar dataKey="count" fill={chartTheme.bar} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Distribuição por source_provider">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data.by_source_provider}
              dataKey="count"
              nameKey="source_provider"
              cx="50%"
              cy="50%"
              outerRadius={90}
              label={({ source_provider, count }) => `${source_provider}: ${count}`}
            >
              {data.by_source_provider.map((_, index) => (
                <Cell key={index} fill={chartTheme.pie[index % chartTheme.pie.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ color: chartTheme.axis }} />
          </PieChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Tendência — últimos 7 dias">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.grid} />
            <XAxis dataKey="label" tick={{ fontSize: 11, fill: chartTheme.axis }} />
            <YAxis allowDecimals={false} tick={{ fill: chartTheme.axis }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Line
              type="monotone"
              dataKey="count"
              stroke={chartTheme.line}
              strokeWidth={2}
              dot={{ fill: chartTheme.line }}
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title={`Tasks atrasadas (${data.overdue_tasks.count})`}>
        {data.overdue_tasks.items.length === 0 ? (
          <p className="flex h-full items-center justify-center text-sm text-muted">
            Nenhuma task atrasada.
          </p>
        ) : (
          <div className="h-full overflow-y-auto pr-1">
            <table className="min-w-full text-left text-sm">
              <thead className="sticky top-0 bg-surface text-muted">
                <tr>
                  <th className="pb-2 pr-2">Título</th>
                  <th className="pb-2 pr-2">Status</th>
                  <th className="pb-2 pr-2">Provider</th>
                  <th className="pb-2">Vencimento</th>
                </tr>
              </thead>
              <tbody>
                {data.overdue_tasks.items.map((task) => (
                  <tr key={`${task.source_provider}:${task.source_id}`} className="border-t border-border">
                    <td className="py-2 pr-2 font-medium text-foreground">{task.title}</td>
                    <td className="py-2 pr-2 text-muted-foreground">{task.status}</td>
                    <td className="py-2 pr-2 text-muted-foreground">{task.source_provider}</td>
                    <td className="py-2 text-muted-foreground">
                      {task.due_date
                        ? new Date(task.due_date).toLocaleDateString("pt-BR")
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ChartCard>
    </div>
  );
}

function KpiCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <Card>
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-foreground">{value}</p>
      {hint ? <p className="mt-1 text-xs text-muted">{hint}</p> : null}
    </Card>
  );
}

export function CanonicalKpiGrid({ data }: { data: CanonicalDashboardResponse | null }) {
  if (!data) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-24 animate-pulse rounded-xl bg-surface-muted" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard label="Total de tasks" value={data.summary.total_tasks} />
      <KpiCard label="Tasks atrasadas" value={data.summary.overdue_count} />
      <KpiCard label="Status distintos" value={data.summary.status_buckets} />
      <KpiCard label="Providers" value={data.summary.source_providers} />
    </div>
  );
}
