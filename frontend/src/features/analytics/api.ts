import type { AnalyticsResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function fetchAnalytics(
  params?: { projectId?: string; connectionId?: string },
  sourceProvider = "trello",
): Promise<AnalyticsResponse> {
  const search = new URLSearchParams();
  if (params?.connectionId) search.set("connection_id", params.connectionId);
  if (params?.projectId) search.set("project_id", params.projectId);
  if (sourceProvider) search.set("source_provider", sourceProvider);
  const query = search.toString();

  const response = await fetch(
    `${API_URL}/api/v1/dashboards/analytics/${query ? `?${query}` : ""}`,
    { cache: "no-store" },
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  return response.json();
}
