import type {
  TrelloConnectResponse,
  TrelloStatusResponse,
  TrelloSyncResponse,
} from "./types";
import { getApiBaseUrl } from "@/lib/api-url";

const API_URL = getApiBaseUrl();

const TRELLO_BASE = `${API_URL}/api/v1/data-sources/trello`;

async function requestJson<T>(
  url: string,
  init?: RequestInit,
): Promise<T> {
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

export async function fetchTrelloStatus(
  connectionId?: string,
  boardId?: string,
): Promise<TrelloStatusResponse> {
  const params = new URLSearchParams();
  if (connectionId) params.set("connection_id", connectionId);
  if (boardId) params.set("board_id", boardId);
  const query = params.toString();
  return requestJson<TrelloStatusResponse>(
    `${TRELLO_BASE}/status/${query ? `?${query}` : ""}`,
  );
}

export async function connectTrello(payload: {
  api_key: string;
  api_token: string;
  board_id?: string;
  workspace_id?: string;
  name?: string;
}): Promise<TrelloConnectResponse> {
  return requestJson<TrelloConnectResponse>(`${TRELLO_BASE}/connect/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function syncTrello(payload?: {
  connection_id?: string;
  board_id?: string;
}): Promise<TrelloSyncResponse> {
  return requestJson<TrelloSyncResponse>(`${TRELLO_BASE}/sync/`, {
    method: "POST",
    body: JSON.stringify(payload || {}),
  });
}
