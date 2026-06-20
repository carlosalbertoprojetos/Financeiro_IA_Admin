"use client";

import type { ReactNode } from "react";

import { useAuth } from "@/shared/auth/AuthProvider";
import { hasRole, type TIPRoleKey } from "@/shared/roles";
import { Alert } from "@/shared/ui";

interface RoleGuardProps {
  role: TIPRoleKey | TIPRoleKey[];
  children: ReactNode;
  fallback?: ReactNode;
}

export function RoleGuard({ role, children, fallback }: RoleGuardProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <Alert variant="info" className="p-6">
        Verificando perfil…
      </Alert>
    );
  }

  if (!hasRole(user?.role, role)) {
    return (
      fallback ?? (
        <Alert variant="warning" className="p-6">
          <p className="font-medium">Perfil insuficiente</p>
          <p className="mt-1 text-sm">
            Perfil necessário:{" "}
            <code className="font-mono">{Array.isArray(role) ? role.join(" | ") : role}</code>
          </p>
        </Alert>
      )
    );
  }

  return <>{children}</>;
}
