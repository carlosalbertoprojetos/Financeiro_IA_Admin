"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { BottlenecksResponse, OverviewResponse, ProductivityResponse } from "@/lib/types";

const PIE_COLORS = ["#2563eb", "#059669", "#dc2626", "#d97706", "#7c3aed", "#64748b"];

interface DashboardChartsProps {
  overview: OverviewResponse | null;
  productivity: ProductivityResponse | null;
  bottlenecks: BottlenecksResponse | null;
  statusDistribution: Array<{ status: string; count: number }>;
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-slate-800">{title}</h3>
      <div className="h-72">{children}</div>
    </div>
  );
}

export default function DashboardCharts({
  overview,
  productivity,
  bottlenecks,
  statusDistribution,
}: DashboardChartsProps) {
  const throughputSeries =
    productivity?.throughput.series ||
    overview?.kpis.throughput?.series ||
    [];

  const kpiHours = overview
    ? [
        { name: "Lead", value: overview.kpis.lead_time?.summary?.mean || 0 },
        { name: "Cycle", value: overview.kpis.cycle_time?.summary?.mean || 0 },
        { name: "Aging", value: overview.kpis.aging?.summary?.mean || 0 },
      ]
    : [];

  const rates = overview
    ? [
        { name: "Delay", value: overview.kpis.delay_rate?.summary?.delay_rate_pct || 0 },
        { name: "Rework", value: overview.kpis.rework_rate?.summary?.rework_rate_pct || 0 },
      ]
    : [];

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <ChartCard title="Throughput">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={throughputSeries}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" tick={{ fontSize: 11 }} />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Distribuição por status">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={statusDistribution}
              dataKey="count"
              nameKey="status"
              cx="50%"
              cy="50%"
              outerRadius={90}
              label={({ status, count }) => `${status}: ${count}`}
            >
              {statusDistribution.map((_, index) => (
                <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="KPIs de tempo (h)">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={kpiHours}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#059669" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Gargalos — aging médio por status">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={bottlenecks?.aging_by_status || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="status" tick={{ fontSize: 11 }} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="avg_aging_hours" fill="#dc2626" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Taxas operacionais (%)">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rates}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Bar dataKey="value" fill="#d97706" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}
