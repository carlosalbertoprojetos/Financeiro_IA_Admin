import { TIPPermission, type TIPPermissionKey } from "@/shared/permissions";
import { TIPRole, type TIPRoleKey } from "@/shared/roles";

/** Mirrors backend DEFAULT_ROLE_PERMISSIONS */
export const ROLE_PERMISSIONS: Record<TIPRoleKey, TIPPermissionKey[]> = {
  viewer: [
    TIPPermission.AUTH_LOGIN,
    TIPPermission.AUTH_LOGOUT,
    TIPPermission.DASHBOARD_VIEW,
    TIPPermission.INTEGRATIONS_VIEW,
    TIPPermission.REPORTS_VIEW,
    TIPPermission.ANALYTICS_VIEW,
    TIPPermission.SETTINGS_VIEW,
  ],
  manager: [
    TIPPermission.AUTH_LOGIN,
    TIPPermission.AUTH_LOGOUT,
    TIPPermission.DASHBOARD_VIEW,
    TIPPermission.DASHBOARD_MANAGE,
    TIPPermission.INTEGRATIONS_VIEW,
    TIPPermission.INTEGRATIONS_MANAGE,
    TIPPermission.DATA_SOURCES_SYNC,
    TIPPermission.REPORTS_VIEW,
    TIPPermission.REPORTS_GENERATE,
    TIPPermission.ANALYTICS_VIEW,
    TIPPermission.AI_INSIGHTS_VIEW,
    TIPPermission.EXPORTS_VIEW,
    TIPPermission.SETTINGS_VIEW,
    TIPPermission.SETTINGS_MANAGE,
  ],
  admin: Object.values(TIPPermission),
};

export function permissionsForRole(role: string): TIPPermissionKey[] {
  if (role in ROLE_PERMISSIONS) {
    return ROLE_PERMISSIONS[role as TIPRoleKey];
  }
  return ROLE_PERMISSIONS[TIPRole.VIEWER];
}
