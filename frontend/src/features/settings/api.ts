import type {
  OpenAISection,
  SettingsOverview,
  TrelloSection,
  WorkspaceSection,
} from "./types";
import { getApiBaseUrl } from "@/lib/api-url";

const API_URL = getApiBaseUrl();
const BASE = `${API_URL}/api/v1/settings`;

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });

  const data = (await response.json()) as T & { error?: string };

  if (!response.ok) {
    throw new Error(data.error || `Request failed: ${response.status}`);
  }

  return data;
}

export async function fetchSettings(): Promise<SettingsOverview> {
  return requestJson<SettingsOverview>(`${BASE}/`);
}

export async function updateWorkspaceSettings(
  workspace_name: string,
): Promise<WorkspaceSection> {
  return requestJson<WorkspaceSection>(`${BASE}/workspace/`, {
    method: "PATCH",
    body: JSON.stringify({ workspace_name }),
  });
}

export async function updateOpenAISettings(payload: {
  api_key?: string;
  model?: string;
}): Promise<OpenAISection> {
  return requestJson<OpenAISection>(`${BASE}/openai/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function saveTrelloSettings(payload: {
  api_key: string;
  api_token: string;
  board_id?: string;
  workspace_id?: string;
  name?: string;
}): Promise<TrelloSection> {
  return requestJson<TrelloSection>(`${BASE}/trello/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
