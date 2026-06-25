import { TIP_APP_PAGES } from "@/page-views/registry";
import type { TIPPermissionKey } from "@/shared/permissions";
import type { TIPNavigationItem } from "@/shared/types";

export interface NavItem extends Omit<TIPNavigationItem, "path"> {
  href: string;
}

export interface NavGroup {
  id: string;
  label: string;
  items: NavItem[];
}

const NAV_ICONS: Record<string, string> = {
  dashboard: "◫",
  integrations: "⎔",
  reports: "▣",
  analytics: "▤",
  settings: "⚙",
};

export function navIconFor(id: string): string {
  return NAV_ICONS[id] ?? "•";
}

/** Client-side main navigation — mirrors backend apps/navigation.py */
export const MAIN_NAV: NavItem[] = TIP_APP_PAGES.map((page) => ({
  id: page.id,
  label: page.label,
  href: page.path,
  permission: page.permission as TIPPermissionKey,
  icon: navIconFor(page.id),
}));

function navItem(id: string): NavItem {
  const item = MAIN_NAV.find((page) => page.id === id);
  if (!item) {
    throw new Error(`Navigation item not found: ${id}`);
  }
  return item;
}

export const SIDEBAR_NAV_GROUPS: NavGroup[] = [
  {
    id: "overview",
    label: "Visão Geral",
    items: [navItem("dashboard")],
  },
  {
    id: "operation",
    label: "Operação",
    items: [navItem("integrations")],
  },
  {
    id: "intelligence",
    label: "Inteligência e Relatórios",
    items: [navItem("analytics"), navItem("reports")],
  },
  {
    id: "administration",
    label: "Administração",
    items: [navItem("settings")],
  },
];
