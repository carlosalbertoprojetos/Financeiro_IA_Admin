import { describe, expect, it } from "vitest";

import { buildBreadcrumbs } from "@/shared/navigation/breadcrumbs";

describe("breadcrumbs", () => {
  it("builds dashboard crumbs", () => {
    expect(buildBreadcrumbs("/dashboard")).toEqual([
      { label: "TIP", href: "/dashboard" },
      { label: "Dashboard" },
    ]);
  });

  it("builds module crumbs", () => {
    expect(buildBreadcrumbs("/reports")).toEqual([
      { label: "TIP", href: "/dashboard" },
      { label: "Relatórios" },
    ]);
  });

  it("handles unknown paths", () => {
    expect(buildBreadcrumbs("/unknown")).toEqual([
      { label: "TIP", href: "/dashboard" },
      { label: "Página" },
    ]);
  });

  it("handles null pathname", () => {
    expect(buildBreadcrumbs(null)).toEqual([
      { label: "TIP", href: "/dashboard" },
      { label: "Dashboard" },
    ]);
  });
});
