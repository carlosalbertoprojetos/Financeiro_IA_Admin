export interface WorkspaceSection {
  id: "workspace";
  label: string;
  status: string;
  workspace_name: string;
  timezone: string;
  editable: boolean;
}

export interface TrelloSection {
  id: "trello";
  label: string;
  status: string;
  configured: boolean;
  summary: string;
  connection_id: string | null;
  board_id: string | null;
  member_username: string | null;
  last_synced_at?: string | null;
}

export interface OpenAISection {
  id: "openai";
  label: string;
  status: string;
  configured: boolean;
  source: "database" | "environment" | "none";
  model: string;
  api_key_masked: string;
  editable: boolean;
}

export interface SettingsOverview {
  module: string;
  status: string;
  sections: {
    workspace: WorkspaceSection;
    trello: TrelloSection;
    openai: OpenAISection;
  };
}

export type SettingsSectionId = keyof SettingsOverview["sections"];
