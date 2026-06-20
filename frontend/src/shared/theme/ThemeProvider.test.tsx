import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ThemeProvider } from "@/shared/theme/ThemeProvider";
import { ThemeToggle } from "@/shared/ui/ThemeToggle";

vi.mock("next-themes", () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useTheme: () => ({
    theme: "light",
    setTheme: vi.fn(),
    resolvedTheme: "light",
  }),
}));

describe("ThemeProvider", () => {
  it("renders children", () => {
    render(
      <ThemeProvider>
        <p>App content</p>
      </ThemeProvider>,
    );
    expect(screen.getByText("App content")).toBeInTheDocument();
  });
});

describe("ThemeToggle", () => {
  it("renders theme selector with options", () => {
    render(<ThemeToggle />);
    const select = screen.getByLabelText("Tema da interface");
    expect(select).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Claro" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Escuro" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Sistema" })).toBeInTheDocument();
  });
});
