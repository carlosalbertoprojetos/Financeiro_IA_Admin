"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  clearSession,
  loadSession,
  loginDemo,
  saveSession,
  type AuthSession,
  type TIPUser,
} from "@/shared/auth/session";
import { hasPermission, type TIPPermissionKey } from "@/shared/permissions";
import { hasRole, roleAtLeast, type TIPRoleKey } from "@/shared/roles";

interface AuthContextValue {
  user: TIPUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, role?: TIPRoleKey) => Promise<void>;
  logout: () => void;
  can: (permission: TIPPermissionKey) => boolean;
  hasRole: (role: TIPRoleKey | TIPRoleKey[]) => boolean;
  roleAtLeast: (minimum: TIPRoleKey) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setSession(loadSession());
    setIsLoading(false);
  }, []);

  const login = useCallback(async (username: string, role?: TIPRoleKey) => {
    const next = await loginDemo(username, role);
    setSession(next);
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setSession(null);
  }, []);

  const can = useCallback(
    (permission: TIPPermissionKey) => {
      if (!session?.user.permissions) return false;
      return hasPermission(session.user.permissions, permission);
    },
    [session],
  );

  const checkRole = useCallback(
    (required: TIPRoleKey | TIPRoleKey[]) => hasRole(session?.user.role, required),
    [session],
  );

  const checkRoleAtLeast = useCallback(
    (minimum: TIPRoleKey) => roleAtLeast(session?.user.role, minimum),
    [session],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user: session?.user ?? null,
      isAuthenticated: Boolean(session),
      isLoading,
      login,
      logout,
      can,
      hasRole: checkRole,
      roleAtLeast: checkRoleAtLeast,
    }),
    [session, isLoading, login, logout, can, checkRole, checkRoleAtLeast],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
