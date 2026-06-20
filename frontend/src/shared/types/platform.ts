import type { TIPPermissionKey } from "@/shared/permissions";

/** Mirrors backend apps/interfaces.py — shared platform contracts. */

export type TIPModuleStatus = "active" | "placeholder";

export interface TIPModuleInfo {
  module: string;
  status: TIPModuleStatus;
  message?: string;
  legacy_path?: string | null;
}

export interface TIPNavigationItem {
  id: string;
  label: string;
  path: string;
  permission: TIPPermissionKey;
  icon: string;
}

export interface TIPUserProfile {
  id: string;
  username: string;
  display_name: string;
  role: string;
  permissions: TIPPermissionKey[];
}

export interface TIPPlatformOverview {
  platform: string;
  name: string;
  version: string;
  modules: Record<string, string>;
}
