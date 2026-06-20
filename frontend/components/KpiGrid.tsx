"use client";

import type { FilteredStats, OverviewResponse } from "@/lib/types";

interface KpiGridProps {
  overview: OverviewResponse | null;
  filteredStats: FilteredStats | null;
  filtersActive: boolean;
}

function KpiCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
      {hint ? <p className="mt-1 text-xs text-slate-400">{hint}</p> : null}
    </div>
  );
}

export default function KpiGrid({ overview, filteredStats, filtersActive }: KpiGridProps) {
  if (!overview) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-24 animate-pulse rounded-xl bg-slate-200" />
        ))}
      </div>
    );
  }

  const kpis = overview.kpis;
  const stats = filtersActive && filteredStats ? filteredStats : null;

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard
        label={filtersActive ? "Cards (filtro)" : "Total de cards"}
        value={stats ? stats.total : overview.summary.total_cards}
        hint={filtersActive ? "Subconjunto filtrado" : undefined}
      />
      <KpiCard
        label="Health score"
        value={`${overview.health_score}%`}
        hint="Índice operacional"
      />
      <KpiCard
        label="Lead time médio (h)"
        value={kpis.lead_time?.summary?.mean ?? 0}
      />
      <KpiCard
        label="Delay rate (%)"
        value={kpis.delay_rate?.summary?.delay_rate_pct ?? 0}
      />
      <KpiCard
        label="Cycle time médio (h)"
        value={kpis.cycle_time?.summary?.mean ?? 0}
      />
      <KpiCard
        label="Aging médio (h)"
        value={stats ? stats.avgAging : kpis.aging?.summary?.mean ?? 0}
      />
      <KpiCard
        label="Conclusão (%)"
        value={overview.summary.completion_rate_pct}
      />
      <KpiCard
        label="Cards atrasados"
        value={stats ? stats.delayed : kpis.delay_rate?.summary?.delayed ?? 0}
      />
    </div>
  );
}
