"use client";

import ReportsView from "@/features/reports/ReportsView";
import { ProtectedPage } from "@/pages/ProtectedPage";
import { TIPPermission } from "@/shared/permissions";

export default function ReportsPage() {
  return <ProtectedPage permission={TIPPermission.REPORTS_VIEW} View={ReportsView} />;
}
