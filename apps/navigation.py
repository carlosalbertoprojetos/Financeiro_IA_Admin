"""Server-driven navigation menu for TIP frontend."""

from apps.interfaces import TIPNavigationItem
from apps.permissions import TIPPermission

TIP_MAIN_NAV: list[TIPNavigationItem] = [
    {
        "id": "dashboard",
        "label": "Dashboard",
        "path": "/dashboard",
        "permission": TIPPermission.DASHBOARD_VIEW,
        "icon": "layout-dashboard",
    },
    {
        "id": "integrations",
        "label": "Integrações",
        "path": "/integrations",
        "permission": TIPPermission.INTEGRATIONS_VIEW,
        "icon": "plug",
    },
    {
        "id": "reports",
        "label": "Relatórios",
        "path": "/reports",
        "permission": TIPPermission.REPORTS_VIEW,
        "icon": "file-text",
    },
    {
        "id": "analytics",
        "label": "Análises",
        "path": "/analytics",
        "permission": TIPPermission.ANALYTICS_VIEW,
        "icon": "bar-chart",
    },
    {
        "id": "settings",
        "label": "Configurações",
        "path": "/settings",
        "permission": TIPPermission.SETTINGS_VIEW,
        "icon": "settings",
    },
]
