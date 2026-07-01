from django.urls import path

from core import system_views

urlpatterns = [
    path("health/", system_views.SystemHealthView.as_view(), name="system-health"),
    path("workspace/", system_views.WorkspaceValidationView.as_view(), name="workspace-validation"),
    path("diagnostics/", system_views.SelfDiagnosticsView.as_view(), name="self-diagnostics"),
    path("usage/", system_views.UsageAnalyticsView.as_view(), name="usage-analytics"),
    path("customer-success/", system_views.CustomerSuccessDashboardView.as_view(), name="customer-success-dashboard"),
    path("licensing/", system_views.LicensingView.as_view(), name="licensing"),
    path("connectors/", system_views.ConnectorFrameworkView.as_view(), name="connector-framework"),
    path("marketplace/", system_views.MarketplaceView.as_view(), name="operational-marketplace"),
    path("demo/", system_views.DemoModeView.as_view(), name="executive-demo-mode"),
    path("onboarding/", system_views.OnboardingView.as_view(), name="customer-onboarding"),
    path("onboarding/state/", system_views.OnboardingStateView.as_view(), name="customer-onboarding-state"),
    path("onboarding/token/", system_views.OnboardingTokenView.as_view(), name="customer-onboarding-token"),
    path("onboarding/discover-boards/", system_views.OnboardingDiscoverBoardsView.as_view(), name="customer-onboarding-discover-boards"),
    path("onboarding/select-boards/", system_views.OnboardingSelectBoardsView.as_view(), name="customer-onboarding-select-boards"),
    path("onboarding/sync/", system_views.OnboardingSyncView.as_view(), name="customer-onboarding-sync"),
    path("onboarding/generate-first-report/", system_views.OnboardingFirstReportView.as_view(), name="customer-onboarding-first-report"),
    path("multi-tenant/", system_views.MultiTenantAuditView.as_view(), name="multi-tenant-audit"),
]
