"use client";

import type { ReactNode } from "react";

import { useAuth } from "@/shared/auth/AuthProvider";
import { TIPPermission, type TIPPermissionKey } from "@/shared/permissions";
import { Alert } from "@/shared/ui";

interface PermissionGuardProps {
  permission: TIPPermissionKey;
  children: ReactNode;
  fallback?: ReactNode;
}

export function PermissionGuard({ permission, children, fallback }: PermissionGuardProps) {
  const { can, isLoading } = useAuth();

  if (isLoading) {
    return (
      <Alert variant="info" className="p-6">
        Verificando permissões…
      </Alert>
    );
  }

  if (!can(permission)) {
    return (
      fallback ?? (
        <Alert variant="warning" className="p-6">
          <p className="font-medium">Acesso restrito</p>
          <p className="mt-1 text-sm">
            Permissão necessária: <code className="font-mono">{permission}</code>
          </p>
        </Alert>
      )
    );
  }

  return <>{children}</>;
}

export { TIPPermission };
