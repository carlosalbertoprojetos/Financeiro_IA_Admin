import AppShell from "@/layouts/AppShell";
import { AuthGate } from "@/layouts/AuthGate";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate>
      <AppShell>{children}</AppShell>
    </AuthGate>
  );
}
