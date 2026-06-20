"use client";

import { useCallback, useEffect, useState } from "react";

import { downloadExecutiveReport, fetchReportsOverview } from "./api";
import type { ReportsOverview } from "./types";
import { useAuth } from "@/shared/auth/AuthProvider";
import { fetchTrelloStatus } from "@/features/integrations/api";
import { TIPPermission } from "@/shared/permissions";
import { Alert, Button, Card } from "@/shared/ui";

export default function ReportsView() {
  const { can } = useAuth();
  const canGenerate = can(TIPPermission.REPORTS_GENERATE);

  const [overview, setOverview] = useState<ReportsOverview | null>(null);
  const [connectionId, setConnectionId] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [lastGeneratedAt, setLastGeneratedAt] = useState<string | null>(null);

  const loadOverview = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const trelloStatus = await fetchTrelloStatus().catch(() => null);
      const activeConnectionId = trelloStatus?.connection_id || undefined;
      setConnectionId(activeConnectionId);

      const reports = await fetchReportsOverview({
        connection_id: activeConnectionId,
        board_id: trelloStatus?.project_id || undefined,
      });
      setOverview(reports);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar relatórios.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  async function handleGenerate() {
    if (!connectionId) {
      setError("Conexão Trello não encontrada. Sincronize em Integrações primeiro.");
      return;
    }

    setGenerating(true);
    setError(null);
    setMessage(null);
    try {
      await downloadExecutiveReport({ connection_id: connectionId });
      const now = new Date().toISOString();
      setLastGeneratedAt(now);
      setMessage("Relatório PDF gerado e baixado com sucesso.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao gerar relatório.");
    } finally {
      setGenerating(false);
    }
  }

  const hasData = overview?.has_data ?? false;
  const tasksCount = overview?.tasks_count ?? 0;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Relatórios</h1>
          <p className="mt-1 text-muted-foreground">
            Relatório executivo PDF a partir dos dados sincronizados do Trello.
          </p>
          {connectionId ? (
            <p className="mt-1 text-xs text-muted">
              Conexão ativa: {connectionId}
              {tasksCount > 0 ? ` · ${tasksCount} task(s) sincronizada(s)` : ""}
            </p>
          ) : null}
        </div>
        {canGenerate ? (
          <Button onClick={handleGenerate} disabled={generating || !hasData || !connectionId}>
            {generating ? "Gerando…" : "Gerar relatório"}
          </Button>
        ) : (
          <span className="rounded-lg border border-border px-3 py-2 text-xs text-muted">
            Geração disponível para Manager+
          </span>
        )}
      </header>

      {loading ? (
        <Alert variant="info" className="p-6">
          Carregando…
        </Alert>
      ) : null}

      {error ? <Alert variant="error">{error}</Alert> : null}
      {message ? <Alert variant="success">{message}</Alert> : null}

      {!loading && !hasData ? (
        <Alert variant="warning">
          Nenhum dado do Trello disponível para a conexão ativa. Sincronize o board em Integrações
          antes de gerar relatórios.
        </Alert>
      ) : null}

      {overview ? (
        <Card className="overflow-hidden p-0">
          <table className="min-w-full divide-y divide-border text-sm">
            <thead className="bg-surface-muted">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Relatório</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Tipo</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Fonte</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Última geração</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Ação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {overview.reports.map((report) => (
                <tr key={report.id}>
                  <td className="px-4 py-3 font-medium text-foreground">{report.label}</td>
                  <td className="px-4 py-3 text-muted-foreground">{report.type}</td>
                  <td className="px-4 py-3 text-muted-foreground">Trello sync</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {lastGeneratedAt
                      ? new Intl.DateTimeFormat("pt-BR", {
                          dateStyle: "short",
                          timeStyle: "short",
                        }).format(new Date(lastGeneratedAt))
                      : "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      disabled={!canGenerate || generating || !hasData || !connectionId}
                      onClick={handleGenerate}
                      className="text-sm font-medium text-primary hover:text-brand-800 disabled:cursor-not-allowed disabled:text-muted"
                    >
                      Baixar PDF
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
    </div>
  );
}
