"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchSettings } from "./api";
import { fetchTrelloStatus } from "@/features/integrations/api";

export interface TrelloConfig {
  boardId: string | null;
  connectionId: string | null;
  configured: boolean;
  boardLabel: string | null;
}

export function useTrelloConfig() {
  const [config, setConfig] = useState<TrelloConfig>({
    boardId: null,
    connectionId: null,
    configured: false,
    boardLabel: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [settings, status] = await Promise.all([
        fetchSettings(),
        fetchTrelloStatus().catch(() => null),
      ]);

      const boardId =
        settings.sections.trello.board_id || status?.project_id || null;

      setConfig({
        boardId,
        connectionId:
          status?.connection_id || settings.sections.trello.connection_id || null,
        configured: settings.sections.trello.configured,
        boardLabel: status?.name || boardId,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar configurações Trello.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  return { ...config, loading, error, reload };
}
