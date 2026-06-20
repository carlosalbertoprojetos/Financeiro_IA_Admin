import type { CardItem, DashboardFilters, FilteredStats } from "./types";

export function filterCards(cards: CardItem[], filters: Pick<DashboardFilters, "collaborator" | "priority">) {
  return cards.filter((card) => {
    const collaboratorMatch =
      filters.collaborator === "all" ||
      card.assignees.some((assignee) => assignee.id === filters.collaborator);

    const priorityMatch = filters.priority === "all" || card.priority === filters.priority;

    return collaboratorMatch && priorityMatch;
  });
}

export function buildFilteredStats(cards: CardItem[]): FilteredStats {
  const open = cards.filter((card) => !card.is_closed).length;
  const completed = cards.filter((card) => card.is_closed).length;
  const delayed = cards.filter((card) => card.is_delayed).length;
  const agingValues = cards
    .map((card) => card.aging_hours)
    .filter((value): value is number => typeof value === "number");
  const avgAging =
    agingValues.length > 0
      ? Math.round((agingValues.reduce((sum, value) => sum + value, 0) / agingValues.length) * 10) / 10
      : 0;

  return {
    total: cards.length,
    open,
    completed,
    delayed,
    avgAging,
  };
}

export function buildStatusDistribution(cards: CardItem[]) {
  const counts = new Map<string, number>();
  cards.forEach((card) => {
    const status = card.status || "Sem status";
    counts.set(status, (counts.get(status) || 0) + 1);
  });

  return Array.from(counts.entries())
    .map(([status, count]) => ({ status, count }))
    .sort((a, b) => b.count - a.count);
}

export function extractCollaborators(cards: CardItem[]) {
  const map = new Map<string, string>();
  cards.forEach((card) => {
    card.assignees.forEach((assignee) => {
      map.set(assignee.id, assignee.name);
    });
  });
  return Array.from(map.entries())
    .map(([id, name]) => ({ id, name }))
    .sort((a, b) => a.name.localeCompare(b.name));
}
