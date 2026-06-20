export type Period = "day" | "week";
export type PriorityFilter = "all" | "high" | "medium" | "low" | "none";

export interface Assignee {
  id: string;
  name: string;
}

export interface CardLabel {
  id: string;
  name: string;
  color: string;
}

export interface CardItem {
  card_id: string;
  title: string;
  status: string;
  is_closed: boolean;
  is_removed: boolean;
  assignees: Assignee[];
  labels: CardLabel[];
  priority: string;
  due_at: string | null;
  lead_time_hours?: number | null;
  cycle_time_hours?: number | null;
  aging_hours?: number | null;
  is_delayed: boolean;
  has_rework: boolean;
  rework_events: number;
}

export interface OverviewResponse {
  board_id: string;
  generated_at: string;
  summary: {
    total_cards: number;
    open_cards: number;
    completed_cards: number;
    total_actions: number;
    completion_rate_pct: number;
  };
  kpis: Record<
    string,
    {
      metric: string;
      unit: string;
      summary: Record<string, number>;
      series?: Array<{ period: string; count: number }>;
    }
  >;
  status_distribution: Array<{ status: string; count: number }>;
  health_score: number;
}

export interface ProductivityResponse {
  throughput: {
    series: Array<{ period: string; count: number }>;
    summary: Record<string, number>;
  };
  team_output: Array<{
    member_id: string;
    member_name: string;
    card_count: number;
    completed_cards: number;
    completion_rate_pct: number;
  }>;
}

export interface BottlenecksResponse {
  wip_by_status: Array<{ status: string; count: number }>;
  aging_by_status: Array<{
    status: string;
    count: number;
    avg_aging_hours: number;
    max_aging_hours: number;
  }>;
  summary: Record<string, number>;
}

export interface CardsResponse {
  cards: CardItem[];
  summary: Record<string, number>;
}

export interface DashboardFilters {
  boardId: string;
  period: Period;
  collaborator: string;
  priority: PriorityFilter;
}

export interface FilteredStats {
  total: number;
  open: number;
  completed: number;
  delayed: number;
  avgAging: number;
}
