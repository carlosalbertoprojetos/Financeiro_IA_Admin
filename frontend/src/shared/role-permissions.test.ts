import { describe, expect, it } from "vitest";

import { permissionsForRole, ROLE_PERMISSIONS } from "@/shared/role-permissions";
import { TIPPermission } from "@/shared/permissions";
import { TIPRole } from "@/shared/roles";

describe("role-permissions", () => {
  it("viewer has view-only permissions", () => {
    const perms = ROLE_PERMISSIONS.viewer;
    expect(perms).toContain(TIPPermission.DASHBOARD_VIEW);
    expect(perms).not.toContain(TIPPermission.INTEGRATIONS_MANAGE);
  });

  it("manager can sync and generate reports", () => {
    const perms = permissionsForRole(TIPRole.MANAGER);
    expect(perms).toContain(TIPPermission.DATA_SOURCES_SYNC);
    expect(perms).toContain(TIPPermission.REPORTS_GENERATE);
  });

  it("admin has all permissions", () => {
    expect(permissionsForRole(TIPRole.ADMIN).length).toBe(Object.values(TIPPermission).length);
  });

  it("unknown role falls back to viewer", () => {
    expect(permissionsForRole("unknown")).toEqual(ROLE_PERMISSIONS.viewer);
  });
});
