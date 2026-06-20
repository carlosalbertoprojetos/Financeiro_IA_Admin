"use client";

import { useEffect, useState } from "react";

import { connectTrello } from "./api";
import { Alert, Button, Input, Modal } from "@/shared/ui";

interface TrelloConnectModalProps {
  open: boolean;
  onClose: () => void;
  onConnected: () => void;
  defaultBoardId?: string;
}

export function TrelloConnectModal({
  open,
  onClose,
  onConnected,
  defaultBoardId = "",
}: TrelloConnectModalProps) {
  const [apiKey, setApiKey] = useState("");
  const [apiToken, setApiToken] = useState("");
  const [boardId, setBoardId] = useState(defaultBoardId);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  useEffect(() => {
    if (open) {
      setBoardId(defaultBoardId);
      setTestResult(null);
    }
  }, [open, defaultBoardId]);

  async function handleTestConnection() {
    if (!apiKey.trim() || !apiToken.trim()) {
      setTestResult({
        type: "error",
        message: "Informe API Key e Token.",
      });
      return;
    }

    if (!boardId.trim()) {
      setTestResult({
        type: "error",
        message: "Informe o Board ID em Configurações.",
      });
      return;
    }

    setTesting(true);
    setTestResult(null);

    try {
      const result = await connectTrello({
        api_key: apiKey.trim(),
        api_token: apiToken.trim(),
        board_id: boardId.trim(),
      });

      const username = result.member?.username || "usuário Trello";
      setTestResult({
        type: "success",
        message: `Conexão validada com sucesso (${username}).`,
      });
      onConnected();
    } catch (err) {
      setTestResult({
        type: "error",
        message: err instanceof Error ? err.message : "Falha ao testar conexão.",
      });
    } finally {
      setTesting(false);
    }
  }

  return (
    <Modal
      open={open}
      title="Conectar Trello"
      description="Informe suas credenciais da API Trello."
      titleId="trello-connect-title"
      onClose={onClose}
      footer={
        <div className="mt-6 flex flex-wrap gap-3">
          <Button onClick={handleTestConnection} disabled={testing}>
            {testing ? "Testando…" : "Testar conexão"}
          </Button>
          <Button variant="secondary" onClick={onClose}>
            Fechar
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        <label className="block">
          <span className="text-sm font-medium text-muted-foreground">API Key</span>
          <Input
            type="text"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Sua API Key"
            autoComplete="off"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-muted-foreground">Token</span>
          <Input
            type="password"
            value={apiToken}
            onChange={(e) => setApiToken(e.target.value)}
            placeholder="Seu Token"
            autoComplete="off"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-muted-foreground">Board ID</span>
          <Input
            type="text"
            value={boardId}
            onChange={(e) => setBoardId(e.target.value)}
            placeholder="ID do board Trello"
            required
          />
          <p className="mt-1 text-xs text-muted">
            Definido em Configurações e usado em dashboard, analytics e relatórios.
          </p>
        </label>
      </div>

      {testResult ? (
        <Alert variant={testResult.type === "success" ? "success" : "error"} className="mt-4">
          {testResult.message}
        </Alert>
      ) : null}
    </Modal>
  );
}
