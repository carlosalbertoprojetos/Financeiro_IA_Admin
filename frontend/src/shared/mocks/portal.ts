import type { CanonicalDashboardResponse } from "@/features/dashboards/types";

export const MOCK_DASHBOARD: CanonicalDashboardResponse = {
  endpoint: "/api/v1/dashboards/metrics/",
  generated_at: new Date().toISOString(),
  filters: { project_id: "demo-board", source_provider: "trello" },
  summary: {
    total_tasks: 128,
    overdue_count: 7,
    status_buckets: 5,
    source_providers: 2,
  },
  tasks_by_status: [
    { status: "Em progresso", count: 42 },
    { status: "Concluído", count: 58 },
    { status: "Backlog", count: 21 },
    { status: "Bloqueado", count: 7 },
  ],
  overdue_tasks: {
    count: 3,
    items: [
      {
        source_id: "c1",
        title: "Revisar sprint backlog",
        status: "Em progresso",
        due_date: "2026-06-10",
        source_provider: "trello",
        project_id: "demo-board",
      },
      {
        source_id: "c2",
        title: "Atualizar métricas de equipe",
        status: "Backlog",
        due_date: "2026-06-12",
        source_provider: "trello",
        project_id: "demo-board",
      },
    ],
  },
  by_source_provider: [
    { source_provider: "trello", count: 98 },
    { source_provider: "jira", count: 30 },
  ],
  trend_7d: [
    { date: "2026-06-12", count: 12 },
    { date: "2026-06-13", count: 15 },
    { date: "2026-06-14", count: 9 },
    { date: "2026-06-15", count: 18 },
    { date: "2026-06-16", count: 14 },
    { date: "2026-06-17", count: 22 },
    { date: "2026-06-18", count: 17 },
  ],
};

export interface MockAnalyticsMetric {
  id: string;
  label: string;
  value: string;
  trend: string;
  trendUp: boolean;
}

export const MOCK_ANALYTICS = {
  summary: [
    { id: "throughput", label: "Throughput (7d)", value: "84 tasks", trend: "+12%", trendUp: true },
    { id: "cycle", label: "Cycle time médio", value: "3.2 dias", trend: "-8%", trendUp: true },
    { id: "wip", label: "WIP atual", value: "42", trend: "+3", trendUp: false },
    { id: "gaps", label: "Gaps detectados", value: "5", trend: "-2", trendUp: true },
  ] satisfies MockAnalyticsMetric[],
  teamLoad: [
    { member: "Ana", tasks: 18, capacity: 85 },
    { member: "Bruno", tasks: 22, capacity: 92 },
    { member: "Carla", tasks: 14, capacity: 70 },
    { member: "Diego", tasks: 19, capacity: 78 },
  ],
  insights: [
    "3 cards sem responsável há mais de 5 dias.",
    "Lista 'Review' com acúmulo acima da média.",
    "Throughput da equipe subiu 12% na última semana.",
  ],
};

export interface MockReport {
  id: string;
  title: string;
  type: string;
  status: "ready" | "scheduled" | "draft";
  lastGenerated: string;
}

export const MOCK_REPORTS: MockReport[] = [
  {
    id: "executive",
    title: "Relatório Executivo Operacional",
    type: "PDF",
    status: "ready",
    lastGenerated: "2026-06-17T14:30:00Z",
  },
  {
    id: "gaps",
    title: "Análise de Gaps",
    type: "PDF",
    status: "scheduled",
    lastGenerated: "2026-06-16T09:00:00Z",
  },
  {
    id: "team",
    title: "Performance de Equipe",
    type: "CSV",
    status: "draft",
    lastGenerated: "2026-06-15T11:20:00Z",
  },
];

export interface MockIntegration {
  id: string;
  label: string;
  connected: boolean;
  lastSync: string | null;
  tasksCount: number;
}

export const MOCK_INTEGRATIONS: MockIntegration[] = [
  { id: "trello", label: "Trello", connected: true, lastSync: "2026-06-18T08:00:00Z", tasksCount: 98 },
  { id: "jira", label: "Jira", connected: false, lastSync: null, tasksCount: 0 },
  { id: "clickup", label: "ClickUp", connected: false, lastSync: null, tasksCount: 0 },
];

export interface MockSettingSection {
  id: string;
  label: string;
  value: string;
  editable: boolean;
}

export const MOCK_SETTINGS: MockSettingSection[] = [
  { id: "workspace", label: "Workspace", value: "Acme Operations", editable: true },
  { id: "trello", label: "Trello API", value: "•••••••• (conectado)", editable: true },
  { id: "openai", label: "OpenAI", value: "Não configurado", editable: true },
  { id: "timezone", label: "Fuso horário", value: "America/Sao_Paulo", editable: false },
];

export function usePortalMocks(): boolean {
  return process.env.NEXT_PUBLIC_PORTAL_MOCKS === "true";
}
