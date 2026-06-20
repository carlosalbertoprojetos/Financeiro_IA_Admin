export interface StatusBucket {
  status: string;
  count: number;
}

export interface ProviderBucket {
  source_provider: string;
  count: number;
}

export interface OverdueTaskItem {
  source_id: string;
  title: string;
  status: string;
  due_date: string | null;
  source_provider: string;
  project_id: string;
}

export interface TrendPoint {
  date: string;
  count: number;
}

export interface CanonicalDashboardResponse {
  endpoint: string;
  generated_at: string;
  filters: {
    project_id: string | null;
    source_provider: string | null;
  };
  summary: {
    total_tasks: number;
    overdue_count: number;
    status_buckets: number;
    source_providers: number;
  };
  tasks_by_status: StatusBucket[];
  overdue_tasks: {
    count: number;
    items: OverdueTaskItem[];
  };
  by_source_provider: ProviderBucket[];
  trend_7d: TrendPoint[];
}

export interface DashboardFilters {
  projectId: string;
  sourceProvider: string;
  connectionId?: string;
}
