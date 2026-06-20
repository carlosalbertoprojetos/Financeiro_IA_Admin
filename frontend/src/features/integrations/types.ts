export type TrelloConnectionStatus = "connected" | "disconnected";

export interface TrelloStatusResponse {
  status: TrelloConnectionStatus;
  provider: string;
  connection_id: string | null;
  name?: string;
  project_id?: string | null;
  workspace_id?: string | null;
  is_account_connection?: boolean;
  member?: {
    id: string;
    username: string;
  };
  last_synced_at: string | null;
  tasks_count: number;
  credentials_configured: boolean;
}

export interface TrelloConnectResponse extends TrelloStatusResponse {
  created?: boolean;
  board?: {
    id: string;
    name: string;
    url: string;
  };
  error?: string;
}

export interface TrelloSyncResponse {
  status: "success" | "error";
  provider?: string;
  connection_id?: string;
  project_id?: string;
  tasks_synced?: number;
  synced_at?: string;
  details?: Record<string, unknown>;
  error?: string;
}

export type ProviderState = "active" | "placeholder";

export interface ProviderDefinition {
  id: string;
  label: string;
  description: string;
  state: ProviderState;
}
