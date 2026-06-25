"""Shared API response shapes for TIP apps (placeholders)."""

from typing import Any, TypedDict


class TIPModuleStatus(TypedDict):
    module: str
    status: str
    message: str
    legacy_path: str | None


class TIPNavigationItem(TypedDict):
    id: str
    label: str
    path: str
    permission: str
    icon: str


class TIPNavigationGroup(TypedDict):
    id: str
    label: str
    items: list[TIPNavigationItem]


class TIPUserProfile(TypedDict):
    id: str
    username: str
    display_name: str
    role: str
    permissions: list[str]


def module_placeholder(
    module: str,
    *,
    legacy_path: str | None = None,
    message: str = "Module registered — implementation pending.",
) -> dict[str, Any]:
    return {
        "module": module,
        "status": "placeholder",
        "message": message,
        "legacy_path": legacy_path,
    }
