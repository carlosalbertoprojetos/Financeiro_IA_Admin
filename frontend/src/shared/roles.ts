/** TIP commercial SaaS roles — mirrors backend apps/permissions.py */
export const TIPRole = {
  ADMIN: "admin",
  MANAGER: "manager",
  VIEWER: "viewer",
} as const;

export type TIPRoleKey = (typeof TIPRole)[keyof typeof TIPRole];

export const TIP_ROLE_LABELS: Record<TIPRoleKey, string> = {
  admin: "Admin",
  manager: "Manager",
  viewer: "Viewer",
};

export function isValidRole(role: string): role is TIPRoleKey {
  return role === TIPRole.ADMIN || role === TIPRole.MANAGER || role === TIPRole.VIEWER;
}

export function hasRole(userRole: string | undefined, required: TIPRoleKey | TIPRoleKey[]): boolean {
  if (!userRole) return false;
  const roles = Array.isArray(required) ? required : [required];
  return roles.includes(userRole as TIPRoleKey);
}

export function roleAtLeast(userRole: string | undefined, minimum: TIPRoleKey): boolean {
  const hierarchy: TIPRoleKey[] = [TIPRole.VIEWER, TIPRole.MANAGER, TIPRole.ADMIN];
  if (!userRole || !isValidRole(userRole)) return false;
  return hierarchy.indexOf(userRole) >= hierarchy.indexOf(minimum);
}
