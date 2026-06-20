export interface ReportDefinition {
  id: string;
  label: string;
  method: string;
  path: string;
  type: string;
}

export interface ReportsOverview {
  module: string;
  status: string;
  has_data: boolean;
  connection_id?: string | null;
  board_id?: string | null;
  tasks_count?: number;
  reports: ReportDefinition[];
  last_generated_at: string | null;
}
