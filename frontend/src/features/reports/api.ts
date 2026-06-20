import type { ReportsOverview } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const BASE = `${API_URL}/api/v1/reports`;

export async function fetchReportsOverview(params?: {
  connection_id?: string;
  board_id?: string;
}): Promise<ReportsOverview> {
  const search = new URLSearchParams();
  if (params?.connection_id) search.set("connection_id", params.connection_id);
  if (params?.board_id) search.set("board_id", params.board_id);
  const query = search.toString();

  const response = await fetch(`${BASE}/${query ? `?${query}` : ""}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Falha ao carregar relatórios: ${response.status}`);
  }
  return response.json();
}

export async function generateExecutiveReport(payload?: {
  board_id?: string;
  connection_id?: string;
}): Promise<Blob> {
  const response = await fetch(`${BASE}/executive/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });

  if (!response.ok) {
    let message = `Falha ao gerar relatório: ${response.status}`;
    try {
      const data = (await response.json()) as { error?: string };
      if (data.error) message = data.error;
    } catch {
      /* not json */
    }
    throw new Error(message);
  }

  return response.blob();
}

function triggerPdfDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export async function downloadExecutiveReport(payload?: {
  board_id?: string;
  connection_id?: string;
}): Promise<void> {
  const blob = await generateExecutiveReport(payload);
  const board = payload?.board_id || "trello";
  triggerPdfDownload(blob, `executive-report-${board}.pdf`);
}
