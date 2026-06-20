"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { fetchCanonicalDashboard } from "./api";
import { CanonicalDashboardCharts, CanonicalKpiGrid } from "./components";
import type { CanonicalDashboardResponse, DashboardFilters } from "./types";
import { useTrelloConfig } from "@/features/settings/useTrelloConfig";
import { Alert, Button, Card, Select } from "@/shared/ui";

const SOURCE_PROVIDERS = [
  { value: "all", label: "Todos os providers" },
  { value: "trello", label: "Trello" },
];

export default function DashboardView() {
  const trello = useTrelloConfig();
  const [filters, setFilters] = useState<DashboardFilters>({
    projectId: "",
    sourceProvider: "trello",
  });
  const [data, setData] = useState<CanonicalDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (trello.boardId) {
      setFilters((current) => ({
        ...current,
        projectId: trello.boardId || "",
        connectionId: trello.connectionId || undefined,
      }));
    }
  }, [trello.boardId, trello.connectionId]);

  const loadData = useCallback(async () => {
    if (!trello.boardId && !trello.connectionId) {
      setLoading(false);
      setData(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetchCanonicalDashboard({
        ...filters,
        projectId: trello.boardId || filters.projectId,
        connectionId: trello.connectionId || filters.connectionId,
      });
      setData(response);
    } catch (err) {
      setData(null);
      setError(err instanceof Error ? err.message : "Falha ao carregar dashboard.");
    } finally {
      setLoading(false);
    }
  }, [filters, trello.boardId, trello.connectionId]);

  useEffect(() => {
    if (!trello.loading && (trello.boardId || trello.connectionId)) {
      loadData();
    } else if (!trello.loading) {
      setLoading(false);
    }
  }, [loadData, trello.loading, trello.boardId, trello.connectionId]);

  const hasData = Boolean(data && data.summary.total_tasks > 0);
  const boardConfigured = Boolean(trello.boardId);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-foreground">Dashboard Operacional</h1>
        <p className="mt-1 text-muted-foreground">
          Métricas a partir das tasks sincronizadas do Trello.
        </p>
        {boardConfigured ? (
          <p className="mt-1 text-xs text-muted">
            Board configurado: <span className="font-medium">{trello.boardLabel}</span>
          </p>
        ) : null}
      </header>

      <Card className="flex flex-wrap items-end gap-4">
        <label className="block min-w-[180px]">
          <span className="text-sm font-medium text-muted-foreground">Provider</span>
          <Select
            value={filters.sourceProvider}
            onChange={(e) =>
              setFilters((current) => ({ ...current, sourceProvider: e.target.value }))
            }
          >
            {SOURCE_PROVIDERS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </label>

        <Button onClick={loadData} disabled={loading || !boardConfigured}>
          {loading ? "Carregando…" : "Atualizar"}
        </Button>

        {data?.generated_at ? (
          <span className="text-sm text-muted">
            Atualizado em {new Date(data.generated_at).toLocaleString("pt-BR")}
          </span>
        ) : null}
      </Card>

      {trello.error ? <Alert variant="error">{trello.error}</Alert> : null}
      {error ? <Alert variant="error">{error}</Alert> : null}

      {!trello.loading && !boardConfigured ? (
        <Alert variant="warning">
          Board Trello não configurado. Defina o Board ID em{" "}
          <Link href="/settings" className="font-medium underline">
            Configurações → Trello
          </Link>{" "}
          e execute um sync em Integrações.
        </Alert>
      ) : null}

      {!loading && boardConfigured && !hasData ? (
        <Alert variant="warning">
          Nenhuma task sincronizada para o board configurado. Execute um sync em Integrações.
        </Alert>
      ) : null}

      {hasData ? (
        <>
          <CanonicalKpiGrid data={data} />
          <CanonicalDashboardCharts data={data} />
        </>
      ) : null}
    </div>
  );
}
