import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  padding?: "sm" | "md" | "lg";
}

const paddingClasses = {
  sm: "p-4",
  md: "p-5",
  lg: "p-6",
};

export function Card({ children, padding = "sm", className = "", ...props }: CardProps) {
  return (
    <div
      className={`rounded-xl border border-border bg-surface shadow-sm ${paddingClasses[padding]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
