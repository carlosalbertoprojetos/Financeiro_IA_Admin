"""TIP permission constants — used by frontend guards and RBAC."""

from enum import Enum


class TIPPermission(str, Enum):
    """Canonical permission strings for TIP modules."""

    # Users
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"

    # Dashboards
    DASHBOARD_VIEW = "dashboard.view"
    DASHBOARD_MANAGE = "dashboard.manage"

    # Data sources
    INTEGRATIONS_VIEW = "integrations.view"
    INTEGRATIONS_MANAGE = "integrations.manage"
    DATA_SOURCES_SYNC = "data_sources.sync"

    # Analytics
    ANALYTICS_VIEW = "analytics.view"

    # Reports
    REPORTS_VIEW = "reports.view"
    REPORTS_GENERATE = "reports.generate"

    # AI
    AI_INSIGHTS_VIEW = "ai_insights.view"
    AI_INSIGHTS_RUN = "ai_insights.run"

    # Exports
    EXPORTS_VIEW = "exports.view"
    EXPORTS_PDF = "exports.pdf"

    # Settings
    SETTINGS_VIEW = "settings.view"
    SETTINGS_MANAGE = "settings.manage"


class TIPRole(str, Enum):
    """Commercial SaaS roles."""

    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"


DEFAULT_ROLE_PERMISSIONS: dict[str, frozenset[TIPPermission]] = {
    TIPRole.VIEWER: frozenset(
        {
            TIPPermission.AUTH_LOGIN,
            TIPPermission.AUTH_LOGOUT,
            TIPPermission.DASHBOARD_VIEW,
            TIPPermission.INTEGRATIONS_VIEW,
            TIPPermission.REPORTS_VIEW,
            TIPPermission.ANALYTICS_VIEW,
            TIPPermission.SETTINGS_VIEW,
        }
    ),
    TIPRole.MANAGER: frozenset(
        {
            TIPPermission.AUTH_LOGIN,
            TIPPermission.AUTH_LOGOUT,
            TIPPermission.DASHBOARD_VIEW,
            TIPPermission.DASHBOARD_MANAGE,
            TIPPermission.INTEGRATIONS_VIEW,
            TIPPermission.INTEGRATIONS_MANAGE,
            TIPPermission.DATA_SOURCES_SYNC,
            TIPPermission.REPORTS_VIEW,
            TIPPermission.REPORTS_GENERATE,
            TIPPermission.ANALYTICS_VIEW,
            TIPPermission.AI_INSIGHTS_VIEW,
            TIPPermission.EXPORTS_VIEW,
            TIPPermission.SETTINGS_VIEW,
            TIPPermission.SETTINGS_MANAGE,
        }
    ),
    TIPRole.ADMIN: frozenset(TIPPermission),
}


def permissions_for_role(role: str) -> frozenset[TIPPermission]:
    return DEFAULT_ROLE_PERMISSIONS.get(role, DEFAULT_ROLE_PERMISSIONS[TIPRole.VIEWER])
