"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

const MODES = [
  { value: "light", label: "Claro" },
  { value: "dark", label: "Escuro" },
  { value: "system", label: "Sistema" },
] as const;

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div
        className="h-9 w-[7.5rem] rounded-lg border border-border bg-surface-muted"
        aria-hidden
      />
    );
  }

  return (
    <select
      value={theme ?? "system"}
      onChange={(e) => setTheme(e.target.value)}
      className="rounded-lg border border-border-strong bg-surface px-2 py-1.5 text-xs font-medium text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
      aria-label="Tema da interface"
    >
      {MODES.map((mode) => (
        <option key={mode.value} value={mode.value}>
          {mode.label}
        </option>
      ))}
    </select>
  );
}
