import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Breadcrumb } from "@/layouts/Breadcrumb";

vi.mock("next/navigation", () => ({
  usePathname: () => "/reports",
}));

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("Breadcrumb", () => {
  it("renders trail for current path", () => {
    render(<Breadcrumb />);
    expect(screen.getByText("TIP")).toBeInTheDocument();
    expect(screen.getByText("Relatórios")).toBeInTheDocument();
  });
});
