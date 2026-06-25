"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/shared/auth/AuthProvider";
import {
  SIDEBAR_NAV_GROUPS,
  type NavGroup,
  type NavItem,
} from "@/shared/navigation/menu";
import type { TIPPermissionKey } from "@/shared/permissions";
import { TIP_ROLE_LABELS } from "@/shared/roles";

interface SidebarProps {
  onNavigate?: () => void;
}

const SIDEBAR_STORAGE_KEY = "tip.sidebar.openGroups";

export function Sidebar({ onNavigate }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout, can } = useAuth();
  const visibleGroups = useMemo(
    () =>
      SIDEBAR_NAV_GROUPS.map((group) => ({
        ...group,
        items: group.items.filter((item) => can(item.permission as TIPPermissionKey)),
      })).filter((group) => group.items.length > 0),
    [can],
  );
  const activeGroupIds = useMemo(
    () =>
      visibleGroups
        .filter((group) => group.items.some((item) => isActivePath(pathname, item.href)))
        .map((group) => group.id),
    [pathname, visibleGroups],
  );
  const [openGroups, setOpenGroups] = useState<string[]>(activeGroupIds);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(SIDEBAR_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          setOpenGroups([...new Set([...parsed, ...activeGroupIds])]);
          return;
        }
      }
    } catch {
      // Ignore malformed persisted state and fall back to the active route.
    }
    setOpenGroups(activeGroupIds);
  }, [activeGroupIds]);

  useEffect(() => {
    try {
      window.localStorage.setItem(SIDEBAR_STORAGE_KEY, JSON.stringify(openGroups));
    } catch {
      // localStorage may be unavailable in privacy modes.
    }
  }, [openGroups]);

  function toggleGroup(groupId: string) {
    setOpenGroups((current) =>
      current.includes(groupId)
        ? current.filter((id) => id !== groupId)
        : [...current, groupId],
    );
  }

  return (
    <aside className="flex h-full w-64 flex-shrink-0 flex-col border-r border-border bg-surface">
      <div className="border-b border-border px-5 py-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-primary">TIP</p>
        <p className="text-sm font-medium text-foreground">Trello Intelligence Platform</p>
      </div>

      <nav className="flex-1 space-y-2 overflow-y-auto p-3">
        {visibleGroups.map((group) => {
          if (group.items.length === 1 && group.id === "overview") {
            const item = group.items[0];
            return (
              <SidebarLink
                key={item.id}
                item={item}
                active={isActivePath(pathname, item.href)}
                onNavigate={onNavigate}
              />
            );
          }

          return (
            <SidebarGroup
              key={group.id}
              group={group}
              pathname={pathname}
              open={openGroups.includes(group.id) || activeGroupIds.includes(group.id)}
              onToggle={() => toggleGroup(group.id)}
              onNavigate={onNavigate}
            />
          );
        })}
      </nav>

      <div className="border-t border-border p-4">
        <p className="truncate text-sm font-medium text-foreground">
          {user?.displayName ?? "Usuário"}
        </p>
        <p className="truncate text-xs text-muted">
          {user?.role ? (TIP_ROLE_LABELS[user.role as keyof typeof TIP_ROLE_LABELS] ?? user.role) : "—"}
        </p>
        <button
          type="button"
          onClick={() => {
            logout();
            window.location.href = "/login";
          }}
          className="mt-3 text-xs font-medium text-muted hover:text-foreground"
        >
          Sair
        </button>
      </div>
    </aside>
  );
}

function SidebarGroup({
  group,
  pathname,
  open,
  onToggle,
  onNavigate,
}: {
  group: NavGroup;
  pathname: string | null;
  open: boolean;
  onToggle: () => void;
  onNavigate?: () => void;
}) {
  const active = group.items.some((item) => isActivePath(pathname, item.href));

  return (
    <div>
      <button
        type="button"
        onClick={onToggle}
        className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide transition ${
          active
            ? "bg-surface-muted text-foreground"
            : "text-muted-foreground hover:bg-surface-muted hover:text-foreground"
        }`}
        aria-expanded={open}
      >
        <span>{group.label}</span>
        <span
          aria-hidden
          className={`transition-transform duration-200 ${open ? "rotate-90" : ""}`}
        >
          ›
        </span>
      </button>
      <div
        className={`grid transition-[grid-template-rows,opacity] duration-200 ease-out ${
          open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
        }`}
      >
        <div className="overflow-hidden">
          <div className="mt-1 space-y-1 pl-2">
            {group.items.map((item) => (
              <SidebarLink
                key={item.id}
                item={item}
                active={isActivePath(pathname, item.href)}
                onNavigate={onNavigate}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function SidebarLink({
  item,
  active,
  onNavigate,
}: {
  item: NavItem;
  active: boolean;
  onNavigate?: () => void;
}) {
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
        active
          ? "bg-primary-muted text-primary-muted-foreground"
          : "text-muted-foreground hover:bg-surface-muted hover:text-foreground"
      }`}
    >
      <span aria-hidden>{item.icon}</span>
      {item.label}
    </Link>
  );
}

function isActivePath(pathname: string | null, href: string): boolean {
  return pathname != null && (pathname === href || pathname.startsWith(`${href}/`));
}
