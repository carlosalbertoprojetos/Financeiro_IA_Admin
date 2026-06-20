import type { ReactNode } from "react";

type AlertVariant = "error" | "warning" | "success" | "info";

interface AlertProps {
  variant?: AlertVariant;
  children: ReactNode;
  className?: string;
}

const variantClasses: Record<AlertVariant, string> = {
  error: "border-destructive/30 bg-destructive-muted text-destructive-foreground",
  warning: "border-warning/30 bg-warning-muted text-warning-foreground",
  success: "border-success/30 bg-success-muted text-success-foreground",
  info: "border-border bg-surface-muted text-muted-foreground",
};

export function Alert({ variant = "info", children, className = "" }: AlertProps) {
  return (
    <div
      className={`rounded-lg border px-4 py-3 text-sm ${variantClasses[variant]} ${className}`}
      role="alert"
    >
      {children}
    </div>
  );
}
