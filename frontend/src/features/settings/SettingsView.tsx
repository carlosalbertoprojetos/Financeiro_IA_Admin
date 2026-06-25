"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchSettings, updateOpenAISettings, updateWorkspaceSettings } from "./api";
import { SettingEditModal } from "./components/SettingEditModal";
import type { SettingsOverview, SettingsSectionId } from "./types";
import { TrelloConnectModal } from "@/features/integrations/TrelloConnectModal";
import { useAuth } from "@/shared/auth/AuthProvider";
import { RoleGuard } from "@/shared/auth/RoleGuard";
import { TIPPermission } from "@/shared/permissions";
import { TIPRole } from "@/shared/roles";
import { Alert, Button, Card } from "@/shared/ui";

function sectionSummary(overview: SettingsOverview, id: SettingsSectionId): string {
  if (id === "workspace") {
    return overview.sections.workspace.workspace_name || "Não configurado";
  }
  if (id === "trello") {
    const board = overview.sections.trello.board_id;
    return board ? `Board ${board}` : overview.sections.trello.summary;
  }
  const openai = overview.sections.openai;
  if (openai.configured) {
    return `${openai.model} · ${openai.api_key_masked || "chave configurada"}`;
  }
  return "Não configurado";
}

function sectionStatusLabel(overview: SettingsOverview, id: SettingsSectionId): string {
  if (id === "workspace") {
    return overview.sections.workspace.workspace_name ? "Configurado" : "Vazio";
  }
  if (id === "trello") {
    return overview.sections.trello.configured ? "Conectado" : "Não configurado";
  }
  return overview.sections.openai.configured ? "Configurado" : "Não configurado";
}

export default function SettingsView() {
  const { can } = useAuth();
  const canManage = can(TIPPermission.SETTINGS_MANAGE);

  const [overview, setOverview] = useState<SettingsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [editing, setEditing] = useState<SettingsSectionId | null>(null);
  const [workspaceName, setWorkspaceName] = useState("");
  const [openaiKey, setOpenaiKey] = useState("");
  const [openaiModel, setOpenaiModel] = useState("gpt-4.1-mini");
  const [saving, setSaving] = useState(false);

  const loadSettings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSettings();
      setOverview(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar configurações.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  function openEditor(id: SettingsSectionId) {
    if (!overview) return;
    setMessage(null);
    if (id === "workspace") {
      setWorkspaceName(overview.sections.workspace.workspace_name);
    }
    if (id === "openai") {
      setOpenaiKey("");
      const section = overview.sections.openai;
      setOpenaiModel(section.model || section.default_model || "gpt-4.1-mini");
    }
    setEditing(id);
  }

  async function handleSaveWorkspace() {
    if (!workspaceName.trim()) {
      setMessage("Informe o nome do workspace.");
      return;
    }
    setSaving(true);
    setMessage(null);
    try {
      await updateWorkspaceSettings(workspaceName.trim());
      setEditing(null);
      setMessage("Workspace salvo com sucesso.");
      await loadSettings();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao salvar workspace.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveOpenAI() {
    setSaving(true);
    setMessage(null);
    try {
      await updateOpenAISettings({
        ...(openaiKey.trim() ? { api_key: openaiKey.trim() } : {}),
        model: openaiModel.trim() || undefined,
      });
      setEditing(null);
      setMessage("Configurações OpenAI salvas.");
      await loadSettings();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Falha ao salvar OpenAI.");
    } finally {
      setSaving(false);
    }
  }

  const sections: SettingsSectionId[] = ["workspace", "trello", "openai"];

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-foreground">Configurações</h1>
        <p className="mt-1 text-muted-foreground">
          Credenciais reais do workspace — dados carregados da API.
        </p>
      </header>

      {loading ? (
        <Alert variant="info" className="p-6">
          Carregando configurações…
        </Alert>
      ) : null}

      {error ? <Alert variant="error">{error}</Alert> : null}
      {message ? <Alert variant="success">{message}</Alert> : null}

      {overview ? (
        <Card className="p-0">
          <ul className="divide-y divide-border">
            {sections.map((id) => (
              <li key={id} className="flex items-center justify-between gap-4 px-5 py-4">
                <div className="min-w-0">
                  <p className="font-medium text-foreground">{overview.sections[id].label}</p>
                  <p className="truncate text-sm text-muted">{sectionSummary(overview, id)}</p>
                  <p className="mt-1 text-xs text-muted">{sectionStatusLabel(overview, id)}</p>
                </div>
                {canManage ? (
                  <Button variant="secondary" size="sm" onClick={() => openEditor(id)}>
                    Editar
                  </Button>
                ) : (
                  <span className="text-xs text-muted">Somente leitura</span>
                )}
              </li>
            ))}
            <li className="flex items-center justify-between gap-4 px-5 py-4">
              <div>
                <p className="font-medium text-foreground">Fuso horário</p>
                <p className="text-sm text-muted">{overview.sections.workspace.timezone}</p>
              </div>
              <span className="text-xs text-muted">Fixo</span>
            </li>
          </ul>
        </Card>
      ) : null}

      <SettingEditModal
        open={editing === "workspace"}
        title="Editar Workspace"
        description="Nome exibido para o tenant/workspace."
        onClose={() => setEditing(null)}
        onSubmit={handleSaveWorkspace}
        submitting={saving}
      >
        <label className="block text-sm">
          <span className="font-medium text-muted-foreground">Nome do workspace</span>
          <input
            className="mt-1 w-full rounded-lg border border-border-strong bg-surface px-3 py-2 text-foreground"
            value={workspaceName}
            onChange={(e) => setWorkspaceName(e.target.value)}
            placeholder="Ex.: Operações Acme"
          />
        </label>
      </SettingEditModal>

      <SettingEditModal
        open={editing === "openai"}
        title="Editar OpenAI"
        description="Chave usada para análises com IA. Deixe a chave em branco para manter a atual."
        onClose={() => setEditing(null)}
        onSubmit={handleSaveOpenAI}
        submitting={saving}
      >
        <div className="space-y-4">
          <label className="block text-sm">
            <span className="font-medium text-muted-foreground">API Key</span>
            <input
              type="password"
              className="mt-1 w-full rounded-lg border border-border-strong bg-surface px-3 py-2 text-foreground"
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              placeholder={
                overview?.sections.openai.api_key_masked
                  ? `Atual: ${overview.sections.openai.api_key_masked}`
                  : "sk-..."
              }
              autoComplete="off"
            />
          </label>
          <label className="block text-sm">
            <span className="font-medium text-muted-foreground">Modelo</span>
            <select
              className="mt-1 w-full rounded-lg border border-border-strong bg-surface px-3 py-2 text-foreground"
              value={openaiModel}
              onChange={(e) => setOpenaiModel(e.target.value)}
            >
              {(overview?.sections.openai.available_models || []).map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                  {option.recommended ? " (recomendado)" : ""}
                </option>
              ))}
            </select>
            {overview?.sections.openai.available_models?.find((m) => m.id === openaiModel) ? (
              <p className="mt-1 text-xs text-muted-foreground">
                {
                  overview.sections.openai.available_models.find((m) => m.id === openaiModel)
                    ?.description
                }
              </p>
            ) : null}
          </label>
        </div>
      </SettingEditModal>

      <TrelloConnectModal
        open={editing === "trello"}
        onClose={() => setEditing(null)}
        onConnected={async () => {
          setEditing(null);
          setMessage("Credenciais Trello salvas e validadas.");
          await loadSettings();
        }}
        defaultBoardId={overview?.sections.trello.board_id || ""}
      />

      <RoleGuard role={TIPRole.ADMIN}>
        <div className="rounded-xl border border-primary/30 bg-primary-muted p-5">
          <h2 className="font-semibold text-primary-muted-foreground">Área Admin</h2>
          <p className="mt-1 text-sm text-primary-muted-foreground/80">
            Gestão avançada de tenant e usuários — visível apenas para Admin.
          </p>
        </div>
      </RoleGuard>
    </div>
  );
}
