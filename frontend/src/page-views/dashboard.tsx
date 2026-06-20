"use client";

import DashboardView from "@/features/dashboards/DashboardView";
import { ProtectedPage } from "@/pages/ProtectedPage";
import { TIPPermission } from "@/shared/permissions";

export default function DashboardPage() {
  return <ProtectedPage permission={TIPPermission.DASHBOARD_VIEW} View={DashboardView} />;
}
