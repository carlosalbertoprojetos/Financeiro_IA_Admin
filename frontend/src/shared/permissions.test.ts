import { describe, expect, it } from "vitest";

import {
  hasAllPermissions,
  hasAnyPermission,
  hasPermission,
  TIPPermission,
} from "@/shared/permissions";

describe("permissions", () => {
  const perms = [TIPPermission.DASHBOARD_VIEW, TIPPermission.REPORTS_VIEW];

  it("hasPermission returns true when present", () => {
    expect(hasPermission(perms, TIPPermission.DASHBOARD_VIEW)).toBe(true);
  });

  it("hasPermission returns false when missing", () => {
    expect(hasPermission(perms, TIPPermission.SETTINGS_MANAGE)).toBe(false);
  });

  it("hasAnyPermission checks list", () => {
    expect(hasAnyPermission(perms, [TIPPermission.SETTINGS_MANAGE, TIPPermission.REPORTS_VIEW])).toBe(
      true,
    );
  });

  it("hasAllPermissions checks all", () => {
    expect(
      hasAllPermissions(perms, [TIPPermission.DASHBOARD_VIEW, TIPPermission.REPORTS_VIEW]),
    ).toBe(true);
    expect(
      hasAllPermissions(perms, [TIPPermission.DASHBOARD_VIEW, TIPPermission.SETTINGS_MANAGE]),
    ).toBe(false);
  });
});
