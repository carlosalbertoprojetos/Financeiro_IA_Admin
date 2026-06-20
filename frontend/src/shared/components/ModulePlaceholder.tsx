"use client";

import type { ReactNode } from "react";

import { Card } from "@/shared/ui";

interface ModulePlaceholderProps {
  title: string;
  description: string;
  children?: ReactNode;
}

/** Shared placeholder shell for modules pending full UI implementation. */
export function ModulePlaceholder({ title, description, children }: ModulePlaceholderProps) {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-foreground">{title}</h1>
        <p className="mt-1 text-muted-foreground">{description}</p>
      </header>
      {children ?? (
        <Card className="border-dashed p-8 text-center">
          <p className="text-muted-foreground">Módulo registrado — implementação pendente.</p>
        </Card>
      )}
    </div>
  );
}
