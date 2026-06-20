"use client";

import type { ComponentType, ReactNode } from "react";

import { PermissionGuard } from "@/shared/auth/PermissionGuard";
import type { TIPPermissionKey } from "@/shared/permissions";

interface ProtectedPageProps {
  permission: TIPPermissionKey;
  View: ComponentType;
  fallback?: ReactNode;
}

export function ProtectedPage({ permission, View, fallback }: ProtectedPageProps) {
  return (
    <PermissionGuard permission={permission} fallback={fallback}>
      <View />
    </PermissionGuard>
  );
}
