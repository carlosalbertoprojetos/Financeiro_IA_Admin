import { TIP_APP_PAGES } from "@/page-views/registry";
import type { TIPPermissionKey } from "@/shared/permissions";
import type { TIPNavigationItem } from "@/shared/types";

export interface NavItem extends Omit<TIPNavigationItem, "path"> {
  href: string;
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
