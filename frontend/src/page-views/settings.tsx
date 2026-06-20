"use client";

import SettingsView from "@/features/settings/SettingsView";
import { ProtectedPage } from "@/pages/ProtectedPage";
import { TIPPermission } from "@/shared/permissions";

export default function SettingsPage() {
  return <ProtectedPage permission={TIPPermission.SETTINGS_VIEW} View={SettingsView} />;
}
