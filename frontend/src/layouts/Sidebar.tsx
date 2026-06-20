"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/shared/auth/AuthProvider";
import { MAIN_NAV, type NavItem } from "@/shared/navigation/menu";
import type { TIPPermissionKey } from "@/shared/permissions";
import { TIP_ROLE_LABELS } from "@/shared/roles";

interface SidebarProps {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout, can } = useAuth();

  return (
    <aside className="flex h-full w-64 flex-shrink-0 flex-col border-r border-border bg-surface">
      <div className="border-b border-border px-5 py-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-primary">TIP</p>
        <p className="text-sm font-medium text-foreground">Trello Intelligence Platform</p>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {MAIN_NAV.filter((item) => can(item.permission as TIPPermissionKey)).map((item) => (
          <SidebarLink
            key={item.id}
            item={item}
            active={
              pathname != null &&
              (pathname === item.href || pathname.startsWith(`${item.href}/`))
            }
            onNavigate={onNavigate}
          />
        ))}
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
