"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/shared/auth/AuthProvider";
import { TIPRole, TIP_ROLE_LABELS, type TIPRoleKey } from "@/shared/roles";
import { Alert, Button, Card, Input, Select, ThemeToggle } from "@/shared/ui";

const ROLES: TIPRoleKey[] = [TIPRole.ADMIN, TIPRole.MANAGER, TIPRole.VIEWER];

export default function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("demo");
  const [role, setRole] = useState<TIPRoleKey>(TIPRole.ADMIN);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(username.trim() || "demo", role);
      router.push("/dashboard");
    } catch {
      setError("Não foi possível entrar.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <Card padding="lg" className="w-full max-w-md">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-primary">TIP</p>
            <h1 className="mt-2 text-2xl font-bold text-foreground">Entrar</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Portal SaaS — selecione perfil para testar permissões.
            </p>
          </div>
          <ThemeToggle />
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <label className="block text-sm">
            <span className="font-medium text-muted-foreground">Usuário</span>
            <Input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="demo"
            />
          </label>

          <label className="block text-sm">
            <span className="font-medium text-muted-foreground">Perfil</span>
            <Select value={role} onChange={(e) => setRole(e.target.value as TIPRoleKey)}>
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {TIP_ROLE_LABELS[r]}
                </option>
              ))}
            </Select>
          </label>

          {error ? <Alert variant="error">{error}</Alert> : null}

          <Button type="submit" disabled={submitting} className="w-full py-2.5">
            {submitting ? "Entrando…" : "Entrar"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
