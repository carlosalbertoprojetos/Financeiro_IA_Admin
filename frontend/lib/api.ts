import type {
  BottlenecksResponse,
  CardsResponse,
  DashboardFilters,
  OverviewResponse,
  ProductivityResponse,
} from "./types";
import { getApiBaseUrl } from "./api-url";

const API_URL = getApiBaseUrl();

function buildUrl(path: string, params: Record<string, string>): string {
  const url = new URL(`${API_URL}${path}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value) url.searchParams.set(key, value);
  });
  return url.toString();
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchDashboardData(filters: DashboardFilters) {
  const params = { board_id: filters.boardId, period: filters.period };

  const [overview, productivity, bottlenecks, cards] = await Promise.all([
    fetchJson<OverviewResponse>(buildUrl("/api/dashboard/overview/", params)),
    fetchJson<ProductivityResponse>(buildUrl("/api/dashboard/productivity/", params)),
    fetchJson<BottlenecksResponse>(buildUrl("/api/dashboard/bottlenecks/", params)),
    fetchJson<CardsResponse>(buildUrl("/api/analytics/metrics/cards/", { board_id: filters.boardId })),
  ]);

  return { overview, productivity, bottlenecks, cards };
}
