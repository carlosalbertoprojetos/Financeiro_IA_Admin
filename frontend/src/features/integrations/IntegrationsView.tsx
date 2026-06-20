"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchTrelloStatus, syncTrello } from "./api";
import { TrelloConnectModal } from "./TrelloConnectModal";
import type { ProviderDefinition, TrelloStatusResponse } from "./types";
import { fetchSettings } from "@/features/settings/api";
import { useAuth } from "@/shared/auth/AuthProvider";
import { TIPPermission } from "@/shared/permissions";
import { Alert, Button, Card } from "@/shared/ui";

const STATUS_POLL_MS = 10_000;

const PROVIDERS: ProviderDefinition[] = [
  {
    id: "trello",
    label: "Trello",
    description: "Sincronize boards, listas e cards via API.",
    state: "active",
  },
  {
    id: "jira",
    label: "Jira",
    description: "Importação de issues e sprints — em breve.",
    state: "placeholder",
  },
  {
    id: "clickup",
    label: "ClickUp",
    description: "Tasks e spaces — em breve.",
    state: "placeholder",
  },
];

function formatTimestamp(value: string | null): string {
  if (!value) return "Nunca";
  try {
    return new Intl.DateTimeFormat("pt-BR", {
      dateStyle: "short",
      timeStyle: "medium",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function StatusBadge({ connected }: { connected: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${
        connected
          ? "bg-success-muted text-success-foreground"
          : "bg-surface-muted text-muted-foreground"
      }`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          connected ? "bg-success animate-pulse" : "bg-muted"
        }`}
      />
      {connected ? "Connected" : "Not connected"}
    </span>
  );
}

export default function IntegrationsView() {
  const { can } = useAuth();
  const canManage = can(TIPPermission.INTEGRATIONS_MANAGE);
  const canSync = can(TIPPermission.DATA_SOURCES_SYNC);
  const [trelloStatus, setTrelloStatus] = useState<TrelloStatusResponse | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [settingsBoardId, setSettingsBoardId] = useState("");

  const loadStatus = useCallback(async () => {
    try {
      const data = await fetchTrelloStatus();
      setTrelloStatus(data);
      setStatusError(null);
    } catch (err) {
      setStatusError(err instanceof Error ? err.message : "Falha ao carregar status.");
    } finally {
      setStatusLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, STATUS_POLL_MS);
    return () => clearInterval(interval);
  }, [loadStatus]);

  useEffect(() => {
    fetchSettings()
      .then((settings) => setSettingsBoardId(settings.sections.trello.board_id || ""))
      .catch(() => setSettingsBoardId(""));
  }, [modalOpen]);

  async function handleSyncNow() {
    setSyncing(true);
    setSyncMessage(null);

    try {
      const result = await syncTrello({
        connection_id: trelloStatus?.connection_id || undefined,
        board_id: trelloStatus?.project_id || undefined,
      });

      if (result.status === "success") {
        setSyncMessage(
          `Sync concluído: ${result.tasks_synced ?? 0} task(s) em ${formatTimestamp(result.synced_at || null)}.`,
        );
        await loadStatus();
      } else {
        setSyncMessage(result.error || "Falha na sincronização.");
      }
    } catch (err) {
      setSyncMessage(err instanceof Error ? err.message : "Falha na sincronização.");
    } finally {
      setSyncing(false);
    }
  }

  const trelloConnected = trelloStatus?.status === "connected";

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-foreground">Integrações</h1>
        <p className="mt-1 text-muted-foreground">Conectores de fontes de dados para o TIP.</p>
      </header>

      {statusError ? <Alert variant="warning">{statusError}</Alert> : null}

      {syncMessage ? (
        <Alert variant={syncMessage.startsWith("Sync concluído") ? "success" : "error"}>
          {syncMessage}
        </Alert>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {PROVIDERS.map((provider) => {
          const isTrello = provider.id === "trello";
          const isPlaceholder = provider.state === "placeholder";

          return (
            <Card
              key={provider.id}
              padding="md"
              className={isPlaceholder ? "opacity-75" : undefined}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="font-semibold text-foreground">{provider.label}</h2>
                  <p className="mt-1 text-sm text-muted-foreground">{provider.description}</p>
                </div>
                {isTrello ? (
                  statusLoading ? (
                    <span className="rounded-full bg-surface-muted px-2 py-0.5 text-xs text-muted">
                      …
                    </span>
                  ) : (
                    <StatusBadge connected={trelloConnected} />
                  )
                ) : (
                  <span className="rounded-full bg-surface-muted px-2 py-0.5 text-xs text-muted">
                    Placeholder
                  </span>
                )}
              </div>

              {isTrello && (
                <dl className="mt-4 space-y-2 border-t border-border pt-4 text-sm">
                  <div className="flex justify-between gap-2">
                    <dt className="text-muted">Membro</dt>
                    <dd className="truncate text-right font-medium text-foreground">
                      {trelloStatus?.member?.username || "—"}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-2">
                    <dt className="text-muted">Board</dt>
                    <dd className="truncate text-right font-medium text-foreground">
                      {trelloStatus?.project_id || trelloStatus?.name || "—"}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-2">
                    <dt className="text-muted">Última sync</dt>
                    <dd className="text-right font-medium text-foreground">
                      {statusLoading
                        ? "…"
                        : formatTimestamp(trelloStatus?.last_synced_at ?? null)}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-2">
                    <dt className="text-muted">Tasks</dt>
                    <dd className="font-medium text-foreground">
                      {trelloStatus?.tasks_count ?? 0}
                    </dd>
                  </div>
                </dl>
              )}

              <div className="mt-4 flex flex-wrap gap-2">
                {isTrello ? (
                  <>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setModalOpen(true)}
                      disabled={!canManage}
                    >
                      Conectar
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleSyncNow}
                      disabled={syncing || !trelloConnected || !canSync}
                    >
                      {syncing ? "Sincronizando…" : "Sync Now"}
                    </Button>
                  </>
                ) : (
                  <Button variant="secondary" size="sm" disabled className="cursor-not-allowed">
                    Em breve
                  </Button>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      <TrelloConnectModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onConnected={loadStatus}
        defaultBoardId={settingsBoardId}
      />
    </div>
  );
}
