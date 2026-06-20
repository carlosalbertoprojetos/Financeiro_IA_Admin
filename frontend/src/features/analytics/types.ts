export interface AnalyticsSummaryItem {
  id: string;
  label: string;
  value: string;
}

export interface StatusBucket {
  status: string;
  count: number;
}

export interface TrendPoint {
  date: string;
  count: number;
}

export interface AnalyticsResponse {
  endpoint: string;
  generated_at: string;
  filters: {
    project_id: string | null;
    source_provider: string | null;
  };
  summary: AnalyticsSummaryItem[];
  tasks_by_status: StatusBucket[];
  trend_7d: TrendPoint[];
  overdue_tasks: {
    count: number;
    items: Array<{
      source_id: string;
      title: string;
      status: string;
      due_date: string | null;
    }>;
  };
  insights: string[];
  has_data: boolean;
}
