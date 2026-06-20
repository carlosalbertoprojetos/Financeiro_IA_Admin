"use client";

import type { DashboardFilters, Period, PriorityFilter } from "@/lib/types";

interface FilterBarProps {
  filters: DashboardFilters;
  collaborators: Array<{ id: string; name: string }>;
  onChange: (patch: Partial<DashboardFilters>) => void;
  loading?: boolean;
}

export default function FilterBar({ filters, collaborators, onChange, loading }: FilterBarProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-700">Board ID</span>
          <input
            className="rounded-lg border border-slate-300 px-3 py-2"
            value={filters.boardId}
            onChange={(event) => onChange({ boardId: event.target.value.trim() })}
            placeholder="Trello board ID"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-700">Período</span>
          <select
            className="rounded-lg border border-slate-300 px-3 py-2"
            value={filters.period}
            onChange={(event) => onChange({ period: event.target.value as Period })}
            disabled={loading}
          >
            <option value="day">Diário</option>
            <option value="week">Semanal</option>
          </select>
        </label>

        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-700">Colaborador</span>
          <select
            className="rounded-lg border border-slate-300 px-3 py-2"
            value={filters.collaborator}
            onChange={(event) => onChange({ collaborator: event.target.value })}
            disabled={loading}
          >
            <option value="all">Todos</option>
            {collaborators.map((member) => (
              <option key={member.id} value={member.id}>
                {member.name}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-700">Prioridade</span>
          <select
            className="rounded-lg border border-slate-300 px-3 py-2"
            value={filters.priority}
            onChange={(event) => onChange({ priority: event.target.value as PriorityFilter })}
            disabled={loading}
          >
            <option value="all">Todas</option>
            <option value="high">Alta</option>
            <option value="medium">Média</option>
            <option value="low">Baixa</option>
            <option value="none">Sem prioridade</option>
          </select>
        </label>
      </div>
    </section>
  );
}
