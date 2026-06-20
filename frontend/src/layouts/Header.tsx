"use client";

import { useState } from "react";

import { useAuth } from "@/shared/auth/AuthProvider";
import { Breadcrumb } from "@/layouts/Breadcrumb";
import { TIP_ROLE_LABELS } from "@/shared/roles";
import { ThemeToggle } from "@/shared/ui";

interface HeaderProps {
  onMenuToggle?: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  const { user } = useAuth();

  return (
    <header className="border-b border-border bg-surface px-4 py-3 sm:px-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex min-w-0 flex-1 items-center gap-3">
          <button
            type="button"
            onClick={onMenuToggle}
            className="rounded-lg border border-border p-2 text-muted-foreground hover:bg-surface-muted md:hidden"
            aria-label="Abrir menu"
          >
            ☰
          </button>
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wide text-primary md:hidden">
              TIP
            </p>
            <Breadcrumb />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <div className="hidden items-center gap-3 sm:flex">
            <span className="rounded-full bg-surface-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              {user?.role
                ? (TIP_ROLE_LABELS[user.role as keyof typeof TIP_ROLE_LABELS] ?? user.role)
                : "—"}
            </span>
            <span className="text-sm text-muted-foreground">{user?.displayName ?? "Usuário"}</span>
          </div>
        </div>
      </div>
    </header>
  );
}

export function MobileSidebarOverlay({
  open,
  onClose,
  children,
}: {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
}) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 md:hidden">
      <button
        type="button"
        className="absolute inset-0 bg-overlay/40"
        aria-label="Fechar menu"
        onClick={onClose}
      />
      <div className="absolute left-0 top-0 h-full shadow-xl">{children}</div>
    </div>
  );
}

export function useMobileSidebar() {
  const [open, setOpen] = useState(false);
  return {
    open,
    openSidebar: () => setOpen(true),
    closeSidebar: () => setOpen(false),
  };
}
