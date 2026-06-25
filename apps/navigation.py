"""Server-driven navigation menu for TIP frontend."""

from apps.interfaces import TIPNavigationGroup, TIPNavigationItem
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


def _item(item_id: str) -> TIPNavigationItem:
    for item in TIP_MAIN_NAV:
        if item["id"] == item_id:
            return item
    raise ValueError(f"Navigation item not found: {item_id}")


TIP_SIDEBAR_NAV_GROUPS: list[TIPNavigationGroup] = [
    {
        "id": "overview",
        "label": "Visão Geral",
        "items": [_item("dashboard")],
    },
    {
        "id": "operation",
        "label": "Operação",
        "items": [_item("integrations")],
    },
    {
        "id": "intelligence",
        "label": "Inteligência e Relatórios",
        "items": [_item("analytics"), _item("reports")],
    },
    {
        "id": "administration",
        "label": "Administração",
        "items": [_item("settings")],
    },
]
