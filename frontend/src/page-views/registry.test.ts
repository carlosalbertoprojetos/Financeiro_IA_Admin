import { describe, expect, it } from "vitest";

import { getPageByPath, TIP_APP_PAGES, TIP_PAGES } from "@/page-views/registry";

describe("page registry", () => {
  it("registers all portal routes", () => {
    const paths = TIP_APP_PAGES.map((p) => p.path);
    expect(paths).toEqual([
      "/dashboard",
      "/integrations",
      "/reports",
      "/analytics",
      "/settings",
    ]);
  });

  it("includes login page", () => {
    expect(TIP_PAGES.some((p) => p.path === "/login")).toBe(true);
  });

  it("finds page by path", () => {
    expect(getPageByPath("/analytics")?.label).toBe("Análises");
    expect(getPageByPath("/missing")).toBeUndefined();
  });

  it("lazy-loads all page views", async () => {
    for (const page of TIP_PAGES) {
      const module = await page.loadView();
      expect(module.default).toBeDefined();
    }
  });
});
