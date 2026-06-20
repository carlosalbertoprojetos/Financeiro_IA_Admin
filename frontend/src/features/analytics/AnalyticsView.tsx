"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchAnalytics } from "./api";
import type { AnalyticsResponse } from "./types";
import { fetchTrelloStatus } from "@/features/integrations/api";
import { Alert, Card } from "@/shared/ui";

export default function AnalyticsView() {
  const [connectionId, setConnectionId] = useState<string | undefined>();
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const trelloStatus = await fetchTrelloStatus().catch(() => null);
      const activeConnectionId = trelloStatus?.connection_id || undefined;
      setConnectionId(activeConnectionId);

      const response = await fetchAnalytics({
        connectionId: activeConnectionId,
        projectId: trelloStatus?.project_id || undefined,
      });
      setData(response);
    } catch (err) {
      setData(null);
      setError(err instanceof Error ? err.message : "Falha ao carregar análises.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <Alert variant="info" className="p-6">
        Carregando análises do Trello…
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-foreground">Análises</h1>
        <p className="mt-1 text-muted-foreground">Métricas derivadas das tasks sincronizadas do Trello.</p>
        {connectionId ? (
          <p className="mt-1 text-xs text-muted">Conexão: {connectionId}</p>
        ) : null}
      </header>

      {error ? <Alert variant="error">{error}</Alert> : null}

      {!data?.has_data ? (
        <Alert variant="warning">
          Sem dados do Trello. Execute um sync após conectar suas credenciais.
        </Alert>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {data.summary.map((metric) => (
              <Card key={metric.id}>
                <p className="text-sm text-muted">{metric.label}</p>
                <p className="mt-1 text-2xl font-bold text-foreground">{metric.value}</p>
              </Card>
            ))}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card padding="md">
              <h2 className="font-semibold text-foreground">Tasks por lista/status</h2>
              <ul className="mt-4 space-y-3">
                {data.tasks_by_status.map((row) => (
                  <li key={row.status}>
                    <div className="flex justify-between text-sm">
                      <span className="font-medium text-foreground">{row.status}</span>
                      <span className="text-muted">{row.count}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </Card>

            <Card padding="md">
              <h2 className="font-semibold text-foreground">Insights</h2>
              <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-muted-foreground">
                {data.insights.map((insight) => (
                  <li key={insight}>{insight}</li>
                ))}
              </ul>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
