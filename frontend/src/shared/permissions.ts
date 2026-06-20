/** TIP permission strings — mirrors backend apps/permissions.py */
export const TIPPermission = {
  AUTH_LOGIN: "auth.login",
  AUTH_LOGOUT: "auth.logout",
  DASHBOARD_VIEW: "dashboard.view",
  DASHBOARD_MANAGE: "dashboard.manage",
  INTEGRATIONS_VIEW: "integrations.view",
  INTEGRATIONS_MANAGE: "integrations.manage",
  DATA_SOURCES_SYNC: "data_sources.sync",
  ANALYTICS_VIEW: "analytics.view",
  REPORTS_VIEW: "reports.view",
  REPORTS_GENERATE: "reports.generate",
  AI_INSIGHTS_VIEW: "ai_insights.view",
  AI_INSIGHTS_RUN: "ai_insights.run",
  EXPORTS_VIEW: "exports.view",
  EXPORTS_PDF: "exports.pdf",
  SETTINGS_VIEW: "settings.view",
  SETTINGS_MANAGE: "settings.manage",
} as const;

export type TIPPermissionKey = (typeof TIPPermission)[keyof typeof TIPPermission];

export function hasPermission(
  permissions: string[],
  required: TIPPermissionKey,
): boolean {
  return permissions.includes(required);
}

export function hasAnyPermission(
  permissions: string[],
  required: TIPPermissionKey[],
): boolean {
  return required.some((p) => permissions.includes(p));
}

export function hasAllPermissions(
  permissions: string[],
  required: TIPPermissionKey[],
): boolean {
  return required.every((p) => permissions.includes(p));
}
