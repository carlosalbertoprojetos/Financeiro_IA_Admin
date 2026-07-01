import { getApiBaseUrl } from "@/lib/api-url";

export interface TIPUser {
  id: string;
  username: string;
  displayName: string;
  role: string;
  permissions: string[];
}

export interface AuthSession {
  token: string;
  user: TIPUser;
}

const STORAGE_KEY = "tip_auth_session";

export function loadSession(): AuthSession | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    return null;
  }
}

export function saveSession(session: AuthSession): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearSession(): void {
  localStorage.removeItem(STORAGE_KEY);
}

export async function loginDemo(username: string, role = "admin"): Promise<AuthSession> {
  const apiUrl = getApiBaseUrl();

  try {
    const response = await fetch(`${apiUrl}/api/v1/users/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, role }),
    });

    if (response.ok) {
      const data = await response.json();
      const session: AuthSession = {
        token: data.token,
        user: {
          id: data.user.id,
          username: data.user.username,
          displayName: data.user.display_name,
          role: data.user.role,
          permissions: data.user.permissions,
        },
      };
      saveSession(session);
      return session;
    }
  } catch {
    // Offline demo — fall through to local session
  }

  const { permissionsForRole } = await import("@/shared/role-permissions");
  const session: AuthSession = {
    token: "tip-local-demo-token",
    user: {
      id: "local-demo",
      username,
      displayName: username.charAt(0).toUpperCase() + username.slice(1),
      role,
      permissions: permissionsForRole(role),
    },
  };
  saveSession(session);
  return session;
}
