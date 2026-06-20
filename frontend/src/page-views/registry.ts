import type { ComponentType } from "react";

import { TIPPermission, type TIPPermissionKey } from "@/shared/permissions";

export interface TIPPageDefinition {
  id: string;
  path: string;
  label: string;
  permission: TIPPermissionKey;
  loadView: () => Promise<{ default: ComponentType }>;
  requiresAuth: boolean;
}

export const TIP_PAGES: TIPPageDefinition[] = [
  {
    id: "login",
    path: "/login",
    label: "Entrar",
    permission: TIPPermission.AUTH_LOGIN,
    loadView: () => import("@/page-views/login"),
    requiresAuth: false,
  },
  {
    id: "dashboard",
    path: "/dashboard",
    label: "Dashboard",
    permission: TIPPermission.DASHBOARD_VIEW,
    loadView: () => import("@/features/dashboards"),
    requiresAuth: true,
  },
  {
    id: "integrations",
    path: "/integrations",
    label: "Integrações",
    permission: TIPPermission.INTEGRATIONS_VIEW,
    loadView: () => import("@/features/integrations"),
    requiresAuth: true,
  },
  {
    id: "reports",
    path: "/reports",
    label: "Relatórios",
    permission: TIPPermission.REPORTS_VIEW,
    loadView: () => import("@/features/reports"),
    requiresAuth: true,
  },
  {
    id: "analytics",
    path: "/analytics",
    label: "Análises",
    permission: TIPPermission.ANALYTICS_VIEW,
    loadView: () => import("@/features/analytics"),
    requiresAuth: true,
  },
  {
    id: "settings",
    path: "/settings",
    label: "Configurações",
    permission: TIPPermission.SETTINGS_VIEW,
    loadView: () => import("@/features/settings"),
    requiresAuth: true,
  },
];

export const TIP_APP_PAGES = TIP_PAGES.filter((page) => page.requiresAuth);

export function getPageByPath(path: string): TIPPageDefinition | undefined {
  return TIP_PAGES.find((page) => page.path === path);
}
