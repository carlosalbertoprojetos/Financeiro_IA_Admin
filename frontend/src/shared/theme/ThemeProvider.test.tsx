import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ThemeProvider } from "@/shared/theme/ThemeProvider";
import { ThemeToggle } from "@/shared/ui/ThemeToggle";

const setTheme = vi.fn();

vi.mock("next-themes", () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useTheme: () => ({
    theme: "light",
    setTheme,
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
  it("renders moon button in light mode and toggles to dark", () => {
    render(<ThemeToggle />);

    const button = screen.getByRole("button", { name: "Ativar tema escuro" });
    expect(button).toBeInTheDocument();

    fireEvent.click(button);
    expect(setTheme).toHaveBeenCalledWith("dark");
  });
});
