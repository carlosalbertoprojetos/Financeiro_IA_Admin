import type { CanonicalDashboardResponse, DashboardFilters } from "./types";
import { getApiBaseUrl } from "@/lib/api-url";

const API_URL = getApiBaseUrl();

export async function fetchCanonicalDashboard(
  filters: DashboardFilters,
): Promise<CanonicalDashboardResponse> {
  const params = new URLSearchParams();
  if (filters.connectionId) params.set("connection_id", filters.connectionId);
  if (filters.projectId) params.set("project_id", filters.projectId);
  if (filters.sourceProvider && filters.sourceProvider !== "all") {
    params.set("source_provider", filters.sourceProvider);
  }

  const query = params.toString();
  const url = `${API_URL}/api/v1/dashboards/metrics/${query ? `?${query}` : ""}`;

  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  return response.json();
}
