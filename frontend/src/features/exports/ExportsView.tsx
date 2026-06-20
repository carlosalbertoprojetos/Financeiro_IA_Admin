"use client";

import { ModulePlaceholder } from "@/shared/components/ModulePlaceholder";
import { Alert } from "@/shared/ui";

export default function ExportsView() {
  return (
    <ModulePlaceholder
      title="Exportações"
      description="PDF, CSV e Excel — delegado ao módulo de relatórios."
    >
      <Alert variant="info">
        Exportações PDF/CSV — ver módulo <strong>Relatórios</strong>.
        <p className="mt-2 font-mono text-xs text-muted">GET /api/v1/exports/</p>
      </Alert>
    </ModulePlaceholder>
  );
}
