import { describe, expect, it } from "vitest";

import { MAIN_NAV, navIconFor } from "@/shared/navigation/menu";

describe("menu", () => {
  it("has commercial menu order", () => {
    expect(MAIN_NAV.map((item) => item.label)).toEqual([
      "Dashboard",
      "Integrações",
      "Relatórios",
      "Análises",
      "Configurações",
    ]);
  });

  it("each item has href and permission", () => {
    for (const item of MAIN_NAV) {
      expect(item.href.startsWith("/")).toBe(true);
      expect(item.permission).toBeTruthy();
    }
  });

  it("falls back icon for unknown module", () => {
    expect(navIconFor("unknown")).toBe("•");
  });
});
