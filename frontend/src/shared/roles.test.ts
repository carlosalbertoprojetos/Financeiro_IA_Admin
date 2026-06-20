import { describe, expect, it } from "vitest";

import { hasRole, isValidRole, roleAtLeast, TIPRole } from "@/shared/roles";

describe("roles", () => {
  it("validates known roles", () => {
    expect(isValidRole("admin")).toBe(true);
    expect(isValidRole("guest")).toBe(false);
  });

  it("hasRole matches single and array", () => {
    expect(hasRole("manager", TIPRole.MANAGER)).toBe(true);
    expect(hasRole("viewer", [TIPRole.ADMIN, TIPRole.MANAGER])).toBe(false);
    expect(hasRole(undefined, TIPRole.VIEWER)).toBe(false);
  });

  it("roleAtLeast respects hierarchy", () => {
    expect(roleAtLeast("admin", TIPRole.MANAGER)).toBe(true);
    expect(roleAtLeast("viewer", TIPRole.MANAGER)).toBe(false);
    expect(roleAtLeast(undefined, TIPRole.VIEWER)).toBe(false);
  });
});
