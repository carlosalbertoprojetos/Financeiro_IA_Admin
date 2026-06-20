"use client";

import AnalyticsView from "@/features/analytics/AnalyticsView";
import { ProtectedPage } from "@/pages/ProtectedPage";
import { TIPPermission } from "@/shared/permissions";

export default function AnalyticsPage() {
  return <ProtectedPage permission={TIPPermission.ANALYTICS_VIEW} View={AnalyticsView} />;
}
