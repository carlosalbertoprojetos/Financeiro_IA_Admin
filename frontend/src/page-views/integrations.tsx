"use client";

import IntegrationsView from "@/features/integrations/IntegrationsView";
import { ProtectedPage } from "@/pages/ProtectedPage";
import { TIPPermission } from "@/shared/permissions";

export default function IntegrationsPage() {
  return <ProtectedPage permission={TIPPermission.INTEGRATIONS_VIEW} View={IntegrationsView} />;
}
