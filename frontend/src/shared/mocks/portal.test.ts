import { describe, expect, it } from "vitest";

import { MOCK_ANALYTICS, MOCK_DASHBOARD, MOCK_REPORTS, usePortalMocks } from "@/shared/mocks/portal";

describe("portal mocks", () => {
  it("provides dashboard mock data", () => {
    expect(MOCK_DASHBOARD.summary.total_tasks).toBeGreaterThan(0);
  });

  it("provides analytics mock data", () => {
    expect(MOCK_ANALYTICS.summary.length).toBe(4);
  });

  it("provides reports mock data", () => {
    expect(MOCK_REPORTS.length).toBeGreaterThan(0);
  });

  it("usePortalMocks defaults to false", () => {
    expect(usePortalMocks()).toBe(false);
  });
});
