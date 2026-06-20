import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { RoleGuard } from "@/shared/auth/RoleGuard";
import { TIPRole } from "@/shared/roles";

vi.mock("@/shared/auth/AuthProvider", () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from "@/shared/auth/AuthProvider";

const mockedUseAuth = vi.mocked(useAuth);

describe("RoleGuard", () => {
  it("renders children for matching role", () => {
    mockedUseAuth.mockReturnValue({
      user: { role: TIPRole.ADMIN } as never,
      isLoading: false,
      can: vi.fn(),
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      hasRole: vi.fn(),
      roleAtLeast: vi.fn(),
    });

    render(
      <RoleGuard role={TIPRole.ADMIN}>
        <p>Admin area</p>
      </RoleGuard>,
    );

    expect(screen.getByText("Admin area")).toBeInTheDocument();
  });

  it("blocks insufficient role", () => {
    mockedUseAuth.mockReturnValue({
      user: { role: TIPRole.VIEWER } as never,
      isLoading: false,
      can: vi.fn(),
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      hasRole: vi.fn(),
      roleAtLeast: vi.fn(),
    });

    render(
      <RoleGuard role={TIPRole.ADMIN}>
        <p>Admin area</p>
      </RoleGuard>,
    );

    expect(screen.getByText("Perfil insuficiente")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isLoading: true,
      can: vi.fn(),
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      hasRole: vi.fn(),
      roleAtLeast: vi.fn(),
    });

    render(
      <RoleGuard role={TIPRole.VIEWER}>
        <p>Content</p>
      </RoleGuard>,
    );

    expect(screen.getByText(/Verificando perfil/)).toBeInTheDocument();
  });

  it("accepts any role from array", () => {
    mockedUseAuth.mockReturnValue({
      user: { role: TIPRole.MANAGER } as never,
      isLoading: false,
      can: vi.fn(),
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      hasRole: vi.fn(),
      roleAtLeast: vi.fn(),
    });

    render(
      <RoleGuard role={[TIPRole.ADMIN, TIPRole.MANAGER]}>
        <p>Manager ok</p>
      </RoleGuard>,
    );

    expect(screen.getByText("Manager ok")).toBeInTheDocument();
  });
});
