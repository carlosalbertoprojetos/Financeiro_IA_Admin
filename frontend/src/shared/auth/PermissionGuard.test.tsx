import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PermissionGuard } from "@/shared/auth/PermissionGuard";
import { TIPPermission } from "@/shared/permissions";

vi.mock("@/shared/auth/AuthProvider", () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from "@/shared/auth/AuthProvider";

const mockedUseAuth = vi.mocked(useAuth);

describe("PermissionGuard", () => {
  it("renders children when permission granted", () => {
    mockedUseAuth.mockReturnValue({
      can: () => true,
      isLoading: false,
      user: null,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      hasRole: vi.fn(),
      roleAtLeast: vi.fn(),
    });

    render(
      <PermissionGuard permission={TIPPermission.DASHBOARD_VIEW}>
        <p>Conteúdo protegido</p>
      </PermissionGuard>,
    );

    expect(screen.getByText("Conteúdo protegido")).toBeInTheDocument();
  });

  it("blocks when permission missing", () => {
    mockedUseAuth.mockReturnValue({
      can: () => false,
      isLoading: false,
      user: null,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      hasRole: vi.fn(),
      roleAtLeast: vi.fn(),
    });

    render(
      <PermissionGuard permission={TIPPermission.SETTINGS_MANAGE}>
        <p>Conteúdo protegido</p>
      </PermissionGuard>,
    );

    expect(screen.getByText("Acesso restrito")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    mockedUseAuth.mockReturnValue({
      can: () => false,
      isLoading: true,
      user: null,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      hasRole: vi.fn(),
      roleAtLeast: vi.fn(),
    });

    render(
      <PermissionGuard permission={TIPPermission.DASHBOARD_VIEW}>
        <p>Conteúdo</p>
      </PermissionGuard>,
    );

    expect(screen.getByText(/Verificando permissões/)).toBeInTheDocument();
  });
});
